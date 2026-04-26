import shutil
from pathlib import Path

from config import COLLECTED_DIR, COURSES_DIR, SONGS_DIR
from services.index_store import clean_relative_path, resolve_under
from services.indexer import (
    COLLECTED_THUMBNAILS_DIRNAME,
    build_collected_thumbnail_path,
    scan_collected_video_library,
    scan_course_library,
    scan_song_library,
)


def delete_course_resource(course: dict) -> list[dict]:
    video_path = resolve_under(COURSES_DIR, course.get("video_path", ""))
    lesson_dir = video_path.parent
    relative_lesson_dir = lesson_dir.relative_to(COURSES_DIR.resolve())

    if len(relative_lesson_dir.parts) >= 2:
        _remove_tree(lesson_dir)
    else:
        _remove_file(video_path)
        for material_path in iter_course_file_paths(course):
            _remove_file(resolve_under(COURSES_DIR, material_path))

    return scan_course_library()


def delete_song_resource(song: dict) -> list[dict]:
    song_dir = resolve_under(SONGS_DIR, song.get("path", ""))
    _remove_tree(song_dir)
    prune_empty_parents(song_dir.parent, SONGS_DIR)
    return scan_song_library()


def delete_video_resource(video: dict) -> list[dict]:
    video_path = resolve_under(COLLECTED_DIR, video.get("path", ""))
    _remove_file(video_path)

    thumbnail_relative = clean_relative_path(video.get("thumbnail", ""))
    if thumbnail_relative:
        _remove_file(resolve_under(COLLECTED_DIR, thumbnail_relative))
    else:
        inferred_thumbnail = COLLECTED_DIR / build_collected_thumbnail_path(Path(video.get("path", "")))
        _remove_file(inferred_thumbnail)

    prune_empty_parents(video_path.parent, COLLECTED_DIR)
    prune_empty_parents((COLLECTED_DIR / COLLECTED_THUMBNAILS_DIRNAME).resolve(), COLLECTED_DIR)
    return scan_collected_video_library()


def iter_course_file_paths(course: dict) -> list[str]:
    files = []
    video_path = clean_relative_path(course.get("video_path", ""))
    if video_path:
        files.append(video_path)

    transcript_path = clean_relative_path(course.get("transcript_path", ""))
    if transcript_path:
        files.append(transcript_path)

    materials = course.get("materials") or {}
    for values in materials.values():
        for path in values or []:
            cleaned = clean_relative_path(path)
            if cleaned:
                files.append(cleaned)

    return list(dict.fromkeys(files))


def prune_empty_parents(start: Path, stop: Path) -> None:
    base = stop.resolve()
    current = start.resolve()

    while current != base and base in current.parents:
        if not current.exists() or not current.is_dir():
            current = current.parent
            continue
        if any(current.iterdir()):
            return
        current.rmdir()
        current = current.parent


def _remove_file(path: Path) -> None:
    path.unlink(missing_ok=True)


def _remove_tree(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
