from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, HttpUrl

from services.downloader import SUPPORTED_SOURCES, VideoDownloadError, download_video
from services.index_store import find_video, load_index


router = APIRouter(prefix="/api/videos", tags=["videos"])


class VideoImportRequest(BaseModel):
    url: HttpUrl
    source: str | None = None
    category: str | None = None


@router.get("")
async def list_videos():
    videos = load_index().get("videos", [])
    return [
        {
            "id": video["id"],
            "title": video["title"],
            "source": video.get("source", ""),
            "author": video.get("author", ""),
            "category": video.get("category", ""),
            "path": video.get("path", ""),
            "tags": video.get("tags", []),
            "description": video.get("description", ""),
        }
        for video in videos
    ]


@router.get("/{video_id}")
async def get_video(video_id: str):
    video = find_video(load_index(), video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


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
    videos.insert(0, video)
    index["videos"] = videos

    from services.index_store import save_index

    save_index(index)
    return video
