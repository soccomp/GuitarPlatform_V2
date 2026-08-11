from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from config import COURSES_DIR
from services.ai_assistant import (
    AssistantConfigurationError,
    ask_course_question,
    generate_practice_plan,
)
from services.index_store import clean_relative_path, find_course, load_index, resolve_under, save_index
from services.indexer import scan_course_library
from services.media_response import media_file_response
from services.resource_manager import delete_course_resource
from services.transcriber import TranscriptionError, transcribe_media
from services.course_intelligence import build_course_intelligence
from services.content_backlog import build_course_intelligence_summary
from services.content_relationships import build_related_songs_for_course
from services.content_intelligence_ai import build_ai_content_intelligence, CoachNodeError


router = APIRouter(prefix="/api/courses", tags=["courses"])


def enrich_course(course: dict) -> dict:
    return build_course_intelligence(course, read_course_text(course.get("transcript_path", "")))


async def enrich_course_with_ai(course: dict, coach_model: str = "") -> dict:
    transcript_text = read_course_text(course.get("transcript_path", ""))
    enriched = build_course_intelligence(course, transcript_text)
    if not transcript_text and not enriched.get("description"):
        return enriched

    try:
        ai_fields = await build_ai_content_intelligence(
            content_type="course",
            title=enriched.get("title", ""),
            subtitle=f"{enriched.get('series', '')} / {enriched.get('level', '')}".strip(" /"),
            description=enriched.get("description", ""),
            tags=list(enriched.get("tags") or []),
            transcript_preview=enriched.get("transcript_preview", ""),
            transcript_text=transcript_text,
            coach_model=coach_model,
        )
    except CoachNodeError:
        return enriched

    enriched.update({key: value for key, value in ai_fields.items() if value})
    return enriched


def maybe_persist_enriched_courses(index: dict) -> dict:
    courses = index.get("courses", [])
    enriched = [enrich_course(course) for course in courses]
    if enriched != courses:
        index["courses"] = enriched
        return save_index(index)
    index["courses"] = enriched
    return index


class AskRequest(BaseModel):
    question: str
    transcript: str | None = None


class AskResponse(BaseModel):
    answer: str


class PracticeRequest(BaseModel):
    topic: str
    level: str = "入门"


class PracticeResponse(BaseModel):
    tasks: list[str]
    tips: str


class BatchTranscriptRequest(BaseModel):
    limit: int = 3
    coach_model: str | None = None


@router.get("")
async def list_courses():
    data = maybe_persist_enriched_courses(load_index())
    courses = data.get("courses", [])
    return [
        {
            "id": course["id"],
            "title": course["title"],
            "description": course.get("description", ""),
            "series": course.get("series", ""),
            "level": course.get("level", ""),
            "video_path": course.get("video_path", ""),
            "materials": course.get("materials", {}),
            "tags": course.get("tags", []),
            "transcript_path": course.get("transcript_path", ""),
            "summary": course.get("summary", ""),
            "learning_focus": course.get("learning_focus", ""),
            "recommended_for": course.get("recommended_for", ""),
            "key_points": course.get("key_points", []),
            "transcript_preview": course.get("transcript_preview", ""),
            "transcript_available": course.get("transcript_available", False),
        }
        for course in courses
    ]


@router.get("/scan")
async def scan_courses(persist: bool = False):
    courses = scan_course_library()
    if persist:
        index = load_index()
        index["courses"] = courses
        maybe_persist_enriched_courses(index)
    return {"courses": courses, "persisted": persist}


@router.get("/intelligence-summary")
async def get_course_intelligence_summary():
    index = maybe_persist_enriched_courses(load_index())
    return build_course_intelligence_summary(index)


@router.post("/rebuild-intelligence")
async def rebuild_course_intelligence(body: BatchTranscriptRequest | None = None):
    index = load_index()
    enriched_courses = []
    for course in index.get("courses", []):
        enriched_courses.append(await enrich_course_with_ai(course, coach_model=(body.coach_model if body else "") or ""))
    index["courses"] = enriched_courses
    index = save_index(index)
    return {
        "ok": True,
        "count": len(index.get("courses", [])),
        "courses": index.get("courses", []),
    }


@router.post("/generate-transcripts")
async def generate_course_transcripts(body: BatchTranscriptRequest):
    limit = max(1, min(body.limit, 20))
    index = load_index()
    courses = index.get("courses", [])
    summary = build_course_intelligence_summary(index)
    prioritized_ids = summary.get("prioritized_ids") or []
    pending_pool = [course for course in courses if not (course.get("transcript_path") or "").strip()]
    pending_order = {course.get("id", ""): position for position, course in enumerate(pending_pool)}
    ordered_pending = sorted(
        pending_pool,
        key=lambda item: prioritized_ids.index(item.get("id")) if item.get("id") in prioritized_ids else len(prioritized_ids) + pending_order.get(item.get("id", ""), 0),
    )
    pending = ordered_pending[:limit]

    generated_ids: list[str] = []
    failures: list[dict] = []

    for course in pending:
        video_path = course.get("video_path", "")
        if not video_path:
            failures.append({"id": course.get("id", ""), "title": course.get("title", ""), "error": "No video for this course"})
            continue

        try:
            full_video_path = resolve_under(COURSES_DIR, video_path)
            transcript_relative = course.get("transcript_path", "") or clean_relative_path(
                (Path(video_path).parent / "transcript.md").as_posix()
            )
            full_transcript_path = resolve_under(COURSES_DIR, transcript_relative)
            await run_in_threadpool(transcribe_media, full_video_path, full_transcript_path)
            generated_ids.append(course.get("id", ""))
        except (ValueError, TranscriptionError) as exc:
            failures.append({"id": course.get("id", ""), "title": course.get("title", ""), "error": str(exc)})

    index["courses"] = scan_course_library()
    enriched_courses = []
    for course in index.get("courses", []):
        enriched_courses.append(await enrich_course_with_ai(course, coach_model=body.coach_model or ""))
    index["courses"] = enriched_courses
    index = save_index(index)
    return {
        "ok": True,
        "generated_count": len(generated_ids),
        "generated_ids": generated_ids,
        "failures": failures,
        "courses": index.get("courses", []),
    }


@router.get("/{course_id}")
async def get_course(course_id: str):
    index = maybe_persist_enriched_courses(load_index())
    course = find_course(index, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    enriched = dict(course)
    enriched["related_songs"] = build_related_songs_for_course(course, index)
    return enriched


@router.get("/{course_id}/related-songs")
async def get_course_related_songs(course_id: str):
    index = maybe_persist_enriched_courses(load_index())
    course = find_course(index, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return build_related_songs_for_course(course, index)


@router.delete("/{course_id}")
async def delete_course(course_id: str):
    index = load_index()
    course = find_course(index, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    try:
        courses = delete_course_resource(course)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    index["courses"] = courses
    save_index(index)
    return {"ok": True, "deleted": {"id": course_id, "title": course.get("title", "")}, "courses": courses}


@router.get("/{course_id}/transcript")
async def get_transcript(course_id: str):
    course = find_course(load_index(), course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"content": read_course_text(course.get("transcript_path", ""))}


@router.post("/{course_id}/generate-transcript")
async def generate_transcript(course_id: str, coach_model: str = Query("")):
    index = load_index()
    course = find_course(index, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    video_path = course.get("video_path", "")
    if not video_path:
        raise HTTPException(status_code=404, detail="No video for this course")

    try:
        full_video_path = resolve_under(COURSES_DIR, video_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not full_video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    transcript_relative = course.get("transcript_path", "") or clean_relative_path(
        (Path(video_path).parent / "transcript.md").as_posix()
    )

    try:
        full_transcript_path = resolve_under(COURSES_DIR, transcript_relative)
        await run_in_threadpool(transcribe_media, full_video_path, full_transcript_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TranscriptionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    index["courses"] = scan_course_library()
    refreshed = []
    for item in index.get("courses", []):
        if item.get("id") == course_id:
            refreshed.append(await enrich_course_with_ai(item, coach_model=coach_model))
        else:
            refreshed.append(enrich_course(item))
    index["courses"] = refreshed
    index = save_index(index)
    updated_course = find_course(index, course_id)
    if not updated_course:
        raise HTTPException(status_code=500, detail="Course index refresh failed after transcript generation")

    return {
        "ok": True,
        "course": updated_course,
        "content": read_course_text(updated_course.get("transcript_path", "")),
    }


@router.get("/{course_id}/stream")
async def stream_video(course_id: str, request: Request):
    course = find_course(load_index(), course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    video_path = course.get("video_path", "")
    if not video_path:
        raise HTTPException(status_code=404, detail="No video for this course")

    try:
        full_path = resolve_under(COURSES_DIR, video_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return media_file_response(full_path, request)


@router.post("/{course_id}/ask", response_model=AskResponse)
async def ask_course(course_id: str, body: AskRequest):
    course = find_course(load_index(), course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    transcript = body.transcript or read_course_text(course.get("transcript_path", ""))

    try:
        answer = await ask_course_question(course.get("title", ""), transcript, body.question)
    except AssistantConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc.response.text}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc

    return AskResponse(answer=answer)


@router.post("/generate-practice", response_model=PracticeResponse)
async def generate_practice(body: PracticeRequest):
    try:
        content = await generate_practice_plan(body.topic, body.level)
    except AssistantConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc.response.text}") from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"AI request failed: {exc}") from exc

    lines = [line.strip() for line in content.split("\n") if line.strip()]
    tasks = [line.lstrip("0123456789.📋🎸 ").strip() for line in (lines[:-3] or lines)]
    tips = "\n".join(lines[-3:]) if len(lines) > 3 else ""
    return PracticeResponse(tasks=tasks, tips=tips)


def read_course_text(relative_path: str) -> str:
    if not relative_path:
        return ""

    try:
        full_path = resolve_under(COURSES_DIR, relative_path)
    except ValueError:
        return ""

    if not full_path.exists():
        return ""

    with open(full_path, "r", encoding="utf-8") as handle:
        return handle.read()
