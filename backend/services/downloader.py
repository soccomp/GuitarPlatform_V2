import re
from datetime import datetime, timezone
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import DownloadError

from config import COLLECTED_DIR


SUPPORTED_SOURCES = {"xiaohongshu", "bilibili", "youtube"}


class VideoDownloadError(RuntimeError):
    pass


def download_video(url: str, source_hint: str | None = None, category: str | None = None) -> dict:
    source = normalize_source(source_hint or detect_source(url))
    if source not in SUPPORTED_SOURCES:
        raise VideoDownloadError(f"Unsupported source: {source}")

    target_dir = COLLECTED_DIR / source
    target_dir.mkdir(parents=True, exist_ok=True)

    outtmpl = str(target_dir / "%(title).80s-%(id)s.%(ext)s")
    options = {
        "outtmpl": outtmpl,
        "format": "mp4/bestvideo+bestaudio/best",
        "merge_output_format": "mp4",
        "restrictfilenames": False,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with YoutubeDL(options) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                raise VideoDownloadError("yt-dlp returned no media info")
            downloaded_path = Path(ydl.prepare_filename(info))
    except DownloadError as exc:
        raise VideoDownloadError(str(exc)) from exc

    if downloaded_path.suffix.lower() != ".mp4":
        mp4_candidate = downloaded_path.with_suffix(".mp4")
        if mp4_candidate.exists():
            downloaded_path = mp4_candidate

    if not downloaded_path.exists():
        raise VideoDownloadError("Downloaded file was not found on disk")

    try:
        relative_path = downloaded_path.relative_to(COLLECTED_DIR).as_posix()
    except ValueError as exc:
        raise VideoDownloadError("Downloaded file was saved outside the collected library") from exc

    title = (info.get("title") or downloaded_path.stem or "未命名视频").strip()
    uploader = (info.get("uploader") or info.get("channel") or "").strip()
    tags = [str(tag).strip() for tag in (info.get("tags") or []) if str(tag).strip()][:8]
    description = (info.get("description") or "").strip()[:1000]

    return {
        "id": build_video_id(source, info.get("id") or downloaded_path.stem),
        "type": "collected",
        "title": title,
        "source": source,
        "author": uploader,
        "category": (category or "").strip(),
        "tags": tags,
        "path": relative_path,
        "description": description,
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "original_url": url,
    }


def detect_source(url: str) -> str:
    text = (url or "").lower()
    if "xiaohongshu.com" in text:
        return "xiaohongshu"
    if "bilibili.com" in text or "b23.tv" in text:
        return "bilibili"
    if "youtube.com" in text or "youtu.be" in text:
        return "youtube"
    return "unknown"


def normalize_source(source: str) -> str:
    text = (source or "").strip().lower()
    aliases = {
        "xhs": "xiaohongshu",
        "rednote": "xiaohongshu",
        "b站": "bilibili",
        "yt": "youtube",
    }
    return aliases.get(text, text)


def build_video_id(source: str, raw_id: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", str(raw_id).lower()).strip("-")
    suffix = cleaned or "untitled"
    return f"video_{source}_{suffix}"
