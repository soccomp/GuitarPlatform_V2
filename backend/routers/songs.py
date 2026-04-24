from fastapi import APIRouter, HTTPException
import json
from pathlib import Path

router = APIRouter(prefix="/api/songs", tags=["songs"])

DATA_DIR = Path(__file__).parent.parent / "data"
INDEX_FILE = DATA_DIR / "index.json"


def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"songs": []}


@router.get("")
async def list_songs():
    data = load_index()
    songs = data.get("songs", [])
    return [{"id": s["id"], "title": s["title"], "artist": s.get("artist", "")} for s in songs]


@router.get("/{song_id}")
async def get_song(song_id: str):
    data = load_index()
    songs = data.get("songs", [])
    for s in songs:
        if s["id"] == song_id:
            return s
    raise HTTPException(status_code=404, detail="Song not found")