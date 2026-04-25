import hashlib
import re
from pathlib import Path

from config import COURSES_DIR, SONGS_DIR
from services.index_store import clean_relative_path


AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".m4a"}
SCORE_EXTENSIONS = {".gp", ".gp5", ".gpx", ".gpzip", ".pdf"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".avi", ".mkv", ".webm"}
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
IGNORED_FILENAMES = {".ds_store", ".gitkeep"}


def scan_course_library() -> list[dict]:
    if not COURSES_DIR.exists():
        return []

    courses = []

    for series_dir in sorted([path for path in COURSES_DIR.iterdir() if path.is_dir()]):
        for video_file in sorted(_iter_video_files(series_dir)):
            relative_dir = video_file.parent.relative_to(COURSES_DIR)
            transcript_path = _find_companion_text(video_file.parent)
            material_files = collect_course_materials(video_file.parent, video_file.name)

            courses.append(
                {
                    "id": build_course_id(relative_dir, video_file.stem),
                    "title": video_file.stem,
                    "series": series_dir.name,
                    "level": relative_dir.parts[1] if len(relative_dir.parts) > 1 else relative_dir.parts[0],
                    "description": build_course_description(relative_dir.parts[1:], video_file.stem),
                    "video_path": clean_relative_path(video_file.relative_to(COURSES_DIR).as_posix()),
                    "transcript_path": transcript_path,
                    "tags": list(relative_dir.parts[1:]),
                    "materials": material_files,
                }
            )

    return courses


def scan_song_library() -> list[dict]:
    if not SONGS_DIR.exists():
        return []

    songs = []
    for song_dir in sorted([path for path in SONGS_DIR.iterdir() if path.is_dir()]):
        song = build_song_entry(song_dir)
        if song:
            songs.append(song)

    return songs


def build_song_entry(song_dir: Path, artist: str | None = None) -> dict | None:
    versions = collect_versions(song_dir)
    if not versions:
        return None

    relative_song_dir = song_dir.relative_to(SONGS_DIR)
    artist_name = artist or ""
    song_id = build_song_id(relative_song_dir)

    return {
        "id": song_id,
        "title": song_dir.name,
        "artist": artist_name,
        "path": clean_relative_path(relative_song_dir.as_posix()),
        "versions": versions,
        "markers": [],
    }


def collect_versions(song_dir: Path) -> list[dict]:
    versions = []

    root_files = collect_media_files(song_dir, song_dir)
    if root_files:
        versions.append({"name": "默认版", "files": root_files})

    for media_dir in _iter_media_directories(song_dir):
        if media_dir == song_dir:
            continue
        files = collect_media_files(song_dir, media_dir)
        if not files:
            continue

        relative_dir = media_dir.relative_to(song_dir)
        version_name = " / ".join(relative_dir.parts)
        versions.append({"name": version_name, "files": files})

    return dedupe_versions(versions)


def collect_media_files(song_dir: Path, version_dir: Path) -> dict:
    files: dict[str, str] = {}
    for file_path in sorted([path for path in version_dir.iterdir() if path.is_file()]):
        if file_path.name.lower() in IGNORED_FILENAMES:
            continue
        ext = file_path.suffix.lower()
        relative_path = file_path.relative_to(song_dir).as_posix()
        if ext in AUDIO_EXTENSIONS and "audio" not in files:
            files["audio"] = relative_path
        elif ext in {".gp", ".gp5", ".gpx", ".gpzip"} and "gp" not in files:
            files["gp"] = relative_path
        elif ext == ".pdf" and "pdf" not in files:
            files["pdf"] = relative_path
        elif ext in VIDEO_EXTENSIONS and "video" not in files:
            files["video"] = relative_path
        elif ext in IMAGE_EXTENSIONS and "image" not in files:
            files["image"] = relative_path
    return files


def build_song_id(relative_song_dir: Path) -> str:
    return f"song_{stable_suffix(relative_song_dir.as_posix())}"


def build_course_id(relative_dir: Path, stem: str) -> str:
    seed = f"{relative_dir.as_posix()}-{stem}"
    return f"course_{stable_suffix(seed)}"


def build_course_description(parts: tuple[str, ...], fallback: str) -> str:
    labels = [part for part in parts if part]
    return " / ".join(labels) or fallback


def collect_course_materials(course_dir: Path, video_name: str) -> dict:
    materials = {"pdf": [], "gp": [], "audio": [], "images": []}
    for file_path in sorted([path for path in course_dir.iterdir() if path.is_file()]):
        if file_path.name == video_name or file_path.name.lower() in IGNORED_FILENAMES:
            continue
        ext = file_path.suffix.lower()
        relative = clean_relative_path(file_path.relative_to(COURSES_DIR).as_posix())
        if ext == ".pdf":
            materials["pdf"].append(relative)
        elif ext in {".gp", ".gp5", ".gpx", ".gpzip"}:
            materials["gp"].append(relative)
        elif ext in AUDIO_EXTENSIONS:
            materials["audio"].append(relative)
        elif ext in IMAGE_EXTENSIONS:
            materials["images"].append(relative)
    return {key: value for key, value in materials.items() if value}


def dedupe_versions(versions: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique = []
    for version in versions:
        marker = f"{version['name']}|{sorted(version['files'].items())}"
        if marker in seen:
            continue
        seen.add(marker)
        unique.append(version)
    return unique


def _iter_video_files(root: Path):
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.name.lower() in IGNORED_FILENAMES:
            continue
        if file_path.suffix.lower() in VIDEO_EXTENSIONS:
            yield file_path


def _find_companion_text(course_dir: Path) -> str:
    for candidate_name in ("transcript.md", "notes.md", "practice.md"):
        candidate = course_dir / candidate_name
        if candidate.exists():
            return clean_relative_path(candidate.relative_to(COURSES_DIR).as_posix())
    return ""


def _iter_media_directories(song_dir: Path):
    yield from sorted(
        path
        for path in song_dir.rglob("*")
        if path.is_dir() and any(_is_media_file(file_path) for file_path in path.iterdir() if file_path.is_file())
    )


def _is_media_file(path: Path) -> bool:
    if path.name.lower() in IGNORED_FILENAMES:
        return False
    return path.suffix.lower() in AUDIO_EXTENSIONS.union(SCORE_EXTENSIONS).union(VIDEO_EXTENSIONS).union(IMAGE_EXTENSIONS)


def stable_suffix(seed: str) -> str:
    ascii_slug = re.sub(r"[^a-z0-9]+", "-", seed.lower()).strip("-")
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    return f"{ascii_slug}-{digest}" if ascii_slug else digest
