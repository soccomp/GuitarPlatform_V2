from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter(prefix="/api/videos", tags=["videos"])

DATA_DIR = Path(__file__).parent.parent / "data"
INDEX_FILE = DATA_DIR / "index.json"


def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"videos": []}


@router.get("")
async def list_videos():
    data = load_index()
    videos = data.get("videos", [])
    return [{"id": v["id"], "title": v["title"], "platform": v.get("platform", "")} for v in videos]


@router.get("/{video_id}")
async def get_video(video_id: str):
    data = load_index()
    videos = data.get("videos", [])
    for v in videos:
        if v["id"] == video_id:
            return v
    raise HTTPException(status_code=404, detail="Video not found")