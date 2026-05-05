from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, HttpUrl

from config import COLLECTED_DIR
from services.downloader import SUPPORTED_SOURCES, VideoDownloadError, download_video
from services.index_store import find_video, load_index, resolve_under, save_index
from services.indexer import scan_collected_video_library
from services.media_response import media_file_response
from services.resource_manager import delete_video_resource
from services.video_intelligence import merge_video_intelligence, read_video_transcript_text
from services.transcriber import TranscriptionError, transcribe_media
from services.content_backlog import build_video_intelligence_summary


router = APIRouter(prefix="/api/videos", tags=["videos"])


class VideoImportRequest(BaseModel):
    url: HttpUrl
    source: str | None = None
    category: str | None = None


class VideoUpdateRequest(BaseModel):
    title: str
    author: str | None = None
    category: str | None = None
    description: str | None = None
    tags: list[str] | None = None


class BatchTranscriptRequest(BaseModel):
    limit: int = 3


EDITABLE_VIDEO_FIELDS = ("title", "author", "category", "description", "tags")


def merge_video_metadata(scanned: dict, existing: dict | None) -> dict:
    if not existing:
        return scanned
    merged = dict(scanned)
    for field in EDITABLE_VIDEO_FIELDS:
        if field in existing and existing.get(field) not in (None, ""):
            merged[field] = existing.get(field)
    return merged


def enrich_video(video: dict) -> dict:
    transcript_text = read_video_transcript_text(video.get("transcript_path", ""), COLLECTED_DIR)
    return merge_video_intelligence(video, transcript_text=transcript_text)


def maybe_persist_enriched_videos(index: dict) -> dict:
    videos = index.get("videos", [])
    enriched = [enrich_video(video) for video in videos]
    if enriched != videos:
        index["videos"] = enriched
        return save_index(index)
    index["videos"] = enriched
    return index


def build_video_transcript_relative_path(video: dict) -> str:
    path = Path(video.get("path", ""))
    if not path.name:
        return ""
    return path.with_suffix(".transcript.md").as_posix()


@router.get("")
async def list_videos():
    index = maybe_persist_enriched_videos(load_index())
    videos = index.get("videos", [])
    return [
        {
            "id": video["id"],
            "title": video["title"],
            "source": video.get("source", ""),
            "author": video.get("author", ""),
            "category": video.get("category", ""),
            "path": video.get("path", ""),
            "thumbnail": video.get("thumbnail", ""),
            "tags": video.get("tags", []),
            "description": video.get("description", ""),
            "summary": video.get("summary", ""),
            "learning_focus": video.get("learning_focus", ""),
            "recommended_for": video.get("recommended_for", ""),
            "key_points": video.get("key_points", []),
            "transcript_preview": video.get("transcript_preview", ""),
            "transcript_available": video.get("transcript_available", False),
            "transcript_path": video.get("transcript_path", ""),
        }
        for video in videos
    ]


@router.get("/scan")
async def scan_videos(persist: bool = False):
    videos = scan_collected_video_library()
    if persist:
        index = load_index()
        existing_by_id = {item.get("id"): item for item in index.get("videos", [])}
        index["videos"] = [merge_video_metadata(video, existing_by_id.get(video.get("id"))) for video in videos]
        index = maybe_persist_enriched_videos(index)
        videos = index["videos"]
    return {"videos": videos, "persisted": persist}


@router.post("/rebuild-intelligence")
async def rebuild_video_intelligence():
    index = maybe_persist_enriched_videos(load_index())
    return {
        "ok": True,
        "count": len(index.get("videos", [])),
        "videos": index.get("videos", []),
    }


@router.get("/intelligence-summary")
async def get_video_intelligence_summary():
    index = maybe_persist_enriched_videos(load_index())
    return build_video_intelligence_summary(index)


@router.post("/generate-transcripts")
async def generate_video_transcripts(body: BatchTranscriptRequest):
    limit = max(1, min(body.limit, 20))
    index = load_index()
    videos = index.get("videos", [])
    pending = [video for video in videos if not (video.get("transcript_path") or "").strip()][:limit]

    generated_ids: list[str] = []
    failures: list[dict] = []

    for video in pending:
      try:
        full_video_path = resolve_under(COLLECTED_DIR, video.get("path", ""))
        transcript_relative = build_video_transcript_relative_path(video)
        full_transcript_path = resolve_under(COLLECTED_DIR, transcript_relative)
        await run_in_threadpool(transcribe_media, full_video_path, full_transcript_path)
        generated_ids.append(video.get("id", ""))
      except (ValueError, TranscriptionError) as exc:
        failures.append({"id": video.get("id", ""), "title": video.get("title", ""), "error": str(exc)})

    index["videos"] = scan_collected_video_library()
    index = maybe_persist_enriched_videos(index)
    return {
        "ok": True,
        "generated_count": len(generated_ids),
        "generated_ids": generated_ids,
        "failures": failures,
        "videos": index.get("videos", []),
    }


@router.get("/{video_id}/stream")
async def stream_video(video_id: str, request: Request):
    video = find_video(load_index(), video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        video_path = resolve_under(COLLECTED_DIR, video.get("path", ""))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return media_file_response(video_path, request)


@router.get("/{video_id}/thumbnail")
async def get_video_thumbnail(video_id: str, request: Request):
    video = find_video(load_index(), video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    thumbnail_path = (video.get("thumbnail") or "").strip()
    if not thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not found")

    try:
        asset_path = resolve_under(COLLECTED_DIR, thumbnail_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not asset_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail file not found")

    return media_file_response(asset_path, request)


@router.get("/{video_id}")
async def get_video(video_id: str):
    index = maybe_persist_enriched_videos(load_index())
    video = find_video(index, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.post("/{video_id}/generate-transcript")
async def generate_video_transcript(video_id: str):
    index = load_index()
    video = find_video(index, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        full_video_path = resolve_under(COLLECTED_DIR, video.get("path", ""))
        transcript_relative = video.get("transcript_path", "") or build_video_transcript_relative_path(video)
        full_transcript_path = resolve_under(COLLECTED_DIR, transcript_relative)
        await run_in_threadpool(transcribe_media, full_video_path, full_transcript_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except TranscriptionError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    index["videos"] = scan_collected_video_library()
    index = maybe_persist_enriched_videos(index)
    updated = find_video(index, video_id)
    if not updated:
        raise HTTPException(status_code=500, detail="Video index refresh failed after transcript generation")

    return {
        "ok": True,
        "video": updated,
        "content": read_video_transcript_text(updated.get("transcript_path", ""), COLLECTED_DIR),
    }


@router.patch("/{video_id}")
async def update_video(video_id: str, body: VideoUpdateRequest):
    index = load_index()
    videos = index.get("videos", [])

    for idx, video in enumerate(videos):
        if video.get("id") != video_id:
            continue

        updated = dict(video)
        updated["title"] = body.title.strip() or video.get("title", "")
        updated["author"] = (body.author or "").strip()
        updated["category"] = (body.category or "").strip()
        updated["description"] = (body.description or "").strip()
        updated["tags"] = [str(tag).strip() for tag in (body.tags or updated.get("tags", [])) if str(tag).strip()]
        videos[idx] = enrich_video(updated)
        index["videos"] = videos
        save_index(index)
        return videos[idx]

    raise HTTPException(status_code=404, detail="Video not found")


@router.delete("/{video_id}")
async def delete_video(video_id: str):
    index = load_index()
    video = find_video(index, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    try:
        videos = delete_video_resource(video)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    index["videos"] = videos
    save_index(index)
    return {"ok": True, "deleted": {"id": video_id, "title": video.get("title", "")}, "videos": videos}


@router.post("/import")
async def import_video(body: VideoImportRequest):
    source = (body.source or "").strip().lower()
    if source and source not in SUPPORTED_SOURCES:
        raise HTTPException(status_code=400, detail=f"Unsupported source: {source}")

    try:
        video = await run_in_threadpool(
            download_video,
            str(body.url),
            source or None,
            body.category or None,
        )
    except VideoDownloadError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    index = load_index()
    videos = [item for item in index.get("videos", []) if item.get("id") != video["id"]]
    videos.insert(0, enrich_video(video))
    index["videos"] = videos

    save_index(index)
    return video
