import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from config import COURSES_DIR
from services.ai_assistant import (
    AssistantConfigurationError,
    ask_course_question,
    generate_practice_plan,
)
from services.index_store import find_course, load_index, resolve_under, save_index
from services.indexer import scan_course_library
from services.media_response import media_file_response


router = APIRouter(prefix="/api/courses", tags=["courses"])


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


@router.get("")
async def list_courses():
    data = load_index()
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
        }
        for course in courses
    ]


@router.get("/scan")
async def scan_courses(persist: bool = False):
    courses = scan_course_library()
    if persist:
        index = load_index()
        index["courses"] = courses
        save_index(index)
    return {"courses": courses, "persisted": persist}


@router.get("/{course_id}")
async def get_course(course_id: str):
    course = find_course(load_index(), course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


@router.get("/{course_id}/transcript")
async def get_transcript(course_id: str):
    course = find_course(load_index(), course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"content": read_course_text(course.get("transcript_path", ""))}


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
