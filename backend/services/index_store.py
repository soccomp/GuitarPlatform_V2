import json
from copy import deepcopy
from pathlib import Path

from config import INDEX_FILE


DEFAULT_INDEX = {
    "courses": [],
    "songs": [],
    "videos": [],
}


def load_index() -> dict:
    if not INDEX_FILE.exists():
        return deepcopy(DEFAULT_INDEX)

    with open(INDEX_FILE, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    return normalize_index(raw)


def save_index(data: dict) -> dict:
    normalized = normalize_index(data)
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return normalized


def normalize_index(data: dict | None) -> dict:
    source = data or {}
    return {
        "courses": [normalize_course(course) for course in source.get("courses", [])],
        "songs": [normalize_song(song) for song in source.get("songs", [])],
        "videos": [normalize_video(video) for video in source.get("videos", [])],
    }


def normalize_course(course: dict) -> dict:
    normalized = dict(course)
    normalized.setdefault("description", "")
    normalized.setdefault("series", "未分类课程")
    normalized.setdefault("level", "")
    normalized.setdefault("tags", [])
    normalized.setdefault("video_path", "")
    normalized.setdefault("transcript_path", "")
    return normalized


def normalize_song(song: dict) -> dict:
    normalized = dict(song)
    normalized["path"] = clean_relative_path(normalized.get("path", ""))
    normalized.setdefault("artist", "")
    normalized["versions"] = [normalize_song_version(version) for version in normalized.get("versions", [])]
    normalized["markers"] = [
        {
            "version": marker.get("version", ""),
            "time": marker.get("time", 0),
            "label": marker.get("label", ""),
        }
        for marker in normalized.get("markers", [])
    ]
    return normalized


def normalize_song_version(version: dict) -> dict:
    files = {
        kind: clean_relative_path(path)
        for kind, path in (version.get("files") or {}).items()
        if path
    }
    return {
        "name": version.get("name", "默认版"),
        "files": files,
    }


def normalize_video(video: dict) -> dict:
    normalized = dict(video)
    normalized.setdefault("description", "")
    normalized.setdefault("author", "")
    normalized.setdefault("category", "")
    normalized.setdefault("tags", [])
    normalized.setdefault("source", "unknown")
    normalized.setdefault("type", "collected")
    normalized["path"] = clean_relative_path(normalized.get("path", ""))
    return normalized


def clean_relative_path(value: str) -> str:
    text = (value or "").replace("\\", "/").strip().strip("/")
    return text


def find_course(index: dict, course_id: str) -> dict | None:
    return next((course for course in index.get("courses", []) if course.get("id") == course_id), None)


def find_song(index: dict, song_id: str) -> dict | None:
    return next((song for song in index.get("songs", []) if song.get("id") == song_id), None)


def find_video(index: dict, video_id: str) -> dict | None:
    return next((video for video in index.get("videos", []) if video.get("id") == video_id), None)


def resolve_under(base_dir: Path, relative_path: str) -> Path:
    candidate = (base_dir / clean_relative_path(relative_path)).resolve()
    base = base_dir.resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError(f"Path escapes base directory: {relative_path}")
    return candidate
