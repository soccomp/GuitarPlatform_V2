from fastapi import APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
import json
import os
from pathlib import Path

router = APIRouter(prefix="/api/courses", tags=["courses"])

DATA_DIR = Path(__file__).parent.parent / "data"
INDEX_FILE = DATA_DIR / "index.json"


def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"courses": []}


@router.get("")
async def list_courses():
    data = load_index()
    courses = data.get("courses", [])
    return [{"id": c["id"], "title": c["title"], "description": c.get("description", "")} for c in courses]


@router.get("/{course_id}")
async def get_course(course_id: str):
    data = load_index()
    courses = data.get("courses", [])
    for c in courses:
        if c["id"] == course_id:
            return c
    raise HTTPException(status_code=404, detail="Course not found")


@router.get("/{course_id}/transcript")
async def get_transcript(course_id: str):
    data = load_index()
    courses = data.get("courses", [])
    for c in courses:
        if c["id"] == course_id:
            transcript_path = c.get("transcript_path")
            if not transcript_path:
                return {"content": ""}
            full_path = DATA_DIR.parent / "library" / "courses" / transcript_path
            if os.path.exists(full_path):
                with open(full_path, "r", encoding="utf-8") as f:
                    return {"content": f.read()}
            return {"content": ""}
    raise HTTPException(status_code=404, detail="Course not found")