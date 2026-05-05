from __future__ import annotations

import io
import json
import shutil
import subprocess
import uuid
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

from fastapi import HTTPException

from config import DATA_DIR
from services.index_store import clean_relative_path


COACH_SESSIONS_FILE = DATA_DIR / "coach_sessions.json"
COACH_RECORDINGS_DIR = DATA_DIR / "coach_recordings"


def default_store() -> dict:
    return {"sessions": []}


def load_sessions() -> dict:
    if not COACH_SESSIONS_FILE.exists():
        return default_store()
    with open(COACH_SESSIONS_FILE, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return normalize_store(raw)


def save_sessions(data: dict) -> dict:
    normalized = normalize_store(data)
    COACH_SESSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COACH_SESSIONS_FILE, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return normalized


def normalize_store(data: dict | None) -> dict:
    source = data or {}
    return {
        "sessions": [normalize_session(item) for item in source.get("sessions", [])],
    }


def normalize_session(session: dict) -> dict:
    normalized = deepcopy(session)
    normalized.setdefault("id", "")
    normalized.setdefault("song_id", "")
    normalized.setdefault("song_title", "")
    normalized.setdefault("version", "")
    normalized.setdefault("segment", "")
    normalized.setdefault("tempo_mode", "")
    normalized.setdefault("coach_model", "")
    normalized.setdefault("recording_path", "")
    normalized.setdefault("mixed_path", "")
    normalized.setdefault("recording_mime_type", "audio/webm")
    normalized.setdefault("recording_kind", "audio")
    normalized.setdefault("mixed_mime_type", "")
    normalized.setdefault("mixed_kind", "")
    normalized.setdefault("recording_duration", 0.0)
    normalized.setdefault("reference_label", "")
    normalized.setdefault("reference_asset_path", "")
    normalized.setdefault("created_at", "")
    normalized.setdefault("sync_offset_seconds", 0.0)
    normalized.setdefault("analysis", {})
    normalized["recording_path"] = clean_relative_path(normalized.get("recording_path", ""))
    normalized["mixed_path"] = clean_relative_path(normalized.get("mixed_path", ""))
    normalized["reference_asset_path"] = clean_relative_path(normalized.get("reference_asset_path", ""))
    return normalized


def create_session(
    *,
    song_id: str,
    song_title: str,
    version: str,
    segment_label: str,
    coach_model: str,
    recording_bytes: bytes,
    recording_extension: str,
    recording_mime_type: str,
    recording_kind: str,
    mixed_bytes: bytes | None,
    mixed_extension: str,
    mixed_mime_type: str,
    recorded_duration: float,
    playback_rate: float,
    reference_start_seconds: float,
    sync_offset_seconds: float,
    reference_label: str,
    reference_asset_path: str,
    reference_source_path: Path | None,
    analysis_result: dict,
) -> dict:
    session_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    relative_dir = Path(song_id or "unknown-song") / session_id
    relative_recording_path = relative_dir / f"practice-take.{recording_extension}"
    stored_mixed_extension = mixed_extension or ("mp4" if recording_kind == "video" else "m4a")
    stored_mixed_mime_type = mixed_mime_type or ("video/mp4" if recording_kind == "video" else "audio/mp4")
    relative_mixed_path = relative_dir / f"practice-mix.{stored_mixed_extension}"
    absolute_recording_path = COACH_RECORDINGS_DIR / relative_recording_path
    absolute_mixed_path = COACH_RECORDINGS_DIR / relative_mixed_path
    absolute_recording_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_recording_path.write_bytes(recording_bytes)
    if mixed_bytes:
        absolute_mixed_path.write_bytes(mixed_bytes)
        mixed_created = absolute_mixed_path.exists()
    else:
        mixed_created = create_mixed_practice_media(
            recording_path=absolute_recording_path,
            reference_path=reference_source_path,
            output_path=absolute_mixed_path,
            playback_rate=playback_rate,
            recording_kind=recording_kind,
            reference_start_seconds=reference_start_seconds,
            sync_offset_seconds=sync_offset_seconds,
        )

    session = normalize_session(
        {
            "id": session_id,
            "song_id": song_id,
            "song_title": song_title,
            "version": version,
            "segment": segment_label or version,
            "tempo_mode": analysis_result.get("tempo_mode", ""),
            "coach_model": coach_model,
            "recording_path": relative_recording_path.as_posix(),
            "mixed_path": relative_mixed_path.as_posix() if mixed_created else "",
            "recording_mime_type": recording_mime_type,
            "recording_kind": recording_kind,
            "mixed_mime_type": stored_mixed_mime_type if mixed_created else "",
            "mixed_kind": recording_kind if mixed_created else "",
            "recording_duration": recorded_duration,
            "reference_label": reference_label,
            "reference_asset_path": reference_asset_path,
            "sync_offset_seconds": sync_offset_seconds,
            "created_at": timestamp,
            "analysis": analysis_result,
        }
    )

    data = load_sessions()
    sessions = [item for item in data.get("sessions", []) if item.get("id") != session_id]
    sessions.insert(0, session)
    data["sessions"] = sessions
    save_sessions(data)
    return session


def list_sessions() -> list[dict]:
    return load_sessions().get("sessions", [])


def find_session(session_id: str) -> dict | None:
    return next((item for item in list_sessions() if item.get("id") == session_id), None)


def resolve_recording_path(session: dict) -> Path:
    relative_path = clean_relative_path(session.get("recording_path", ""))
    if not relative_path:
        raise ValueError("Recording path is empty")
    candidate = (COACH_RECORDINGS_DIR / relative_path).resolve()
    base = COACH_RECORDINGS_DIR.resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("Recording path escapes base directory")
    return candidate


def resolve_mixed_path(session: dict) -> Path:
    relative_path = clean_relative_path(session.get("mixed_path", ""))
    if not relative_path:
        raise ValueError("Mixed path is empty")
    candidate = (COACH_RECORDINGS_DIR / relative_path).resolve()
    base = COACH_RECORDINGS_DIR.resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("Mixed path escapes base directory")
    return candidate


def create_mixed_practice_media(
    *,
    recording_path: Path,
    reference_path: Path | None,
    output_path: Path,
    playback_rate: float,
    recording_kind: str,
    reference_start_seconds: float,
    sync_offset_seconds: float,
) -> bool:
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path or not reference_path or not reference_path.exists():
        return False

    sync_delay_ms = max(0, int(round((sync_offset_seconds or 0.0) * 1000)))
    reference_filter = f"[1:a]atempo={max(0.6, min(playback_rate or 1.0, 1.0)):.3f},volume=0.55"
    if sync_delay_ms:
        reference_filter += f",adelay={sync_delay_ms}|{sync_delay_ms}"
    reference_filter += "[a1]"

    audio_mix = f"[0:a]volume=1.8[a0];{reference_filter};[a0][a1]amix=inputs=2:duration=first:dropout_transition=0[aout]"
    if recording_kind == "video":
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(recording_path),
            "-ss",
            f"{max(0.0, reference_start_seconds or 0.0):.3f}",
            "-i",
            str(reference_path),
            "-filter_complex",
            audio_mix,
            "-map",
            "0:v:0",
            "-map",
            "[aout]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-shortest",
            str(output_path),
        ]
    else:
        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(recording_path),
            "-ss",
            f"{max(0.0, reference_start_seconds or 0.0):.3f}",
            "-i",
            str(reference_path),
            "-filter_complex",
            audio_mix,
            "-map",
            "[aout]",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(output_path),
        ]
    try:
        subprocess.run(command, check=True, capture_output=True)
        return output_path.exists()
    except Exception:
        return False


def delete_sessions(session_ids: list[str]) -> dict:
    if not session_ids:
        raise HTTPException(status_code=400, detail="未提供要删除的练习记录")

    data = load_sessions()
    kept: list[dict] = []
    deleted: list[dict] = []

    for session in data.get("sessions", []):
        if session.get("id") not in session_ids:
            kept.append(session)
            continue
        deleted.append(session)
        try:
            recording_path = resolve_recording_path(session)
            if recording_path.exists() and recording_path.is_file():
                recording_path.unlink()
            try:
                mixed_path = resolve_mixed_path(session)
            except ValueError:
                mixed_path = None
            if mixed_path and mixed_path.exists() and mixed_path.is_file():
                mixed_path.unlink()
            parent = recording_path.parent
            if parent.exists() and not any(parent.iterdir()):
                parent.rmdir()
        except ValueError:
            pass

    data["sessions"] = kept
    save_sessions(data)
    return {"ok": True, "deleted": deleted, "sessions": kept}


def export_sessions_zip(session_ids: list[str]) -> tuple[bytes, str]:
    if not session_ids:
        raise HTTPException(status_code=400, detail="未选择要导出的练习记录")

    sessions = [session for session in list_sessions() if session.get("id") in session_ids]
    if not sessions:
        raise HTTPException(status_code=404, detail="未找到要导出的练习记录")

    metadata = []
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for session in sessions:
            recording_name = Path(session.get("recording_path", "")).name
            archive_name = f"{session['song_title']}_{session['id']}/{recording_name}"
            try:
                recording_path = resolve_recording_path(session)
                if recording_path.exists():
                    archive.write(recording_path, archive_name)
            except ValueError:
                pass
            mixed_name = ""
            try:
                mixed_path = resolve_mixed_path(session)
                if mixed_path.exists():
                    mixed_suffix = Path(session.get("mixed_path", "")).suffix or ".m4a"
                    mixed_name = f"{session['song_title']}_{session['id']}/practice-mix{mixed_suffix}"
                    archive.write(mixed_path, mixed_name)
            except ValueError:
                mixed_name = ""
            metadata.append(
                {
                    "id": session.get("id"),
                    "song_title": session.get("song_title"),
                    "version": session.get("version"),
                    "segment": session.get("segment"),
                    "tempo_mode": session.get("tempo_mode"),
                    "coach_model": session.get("coach_model"),
                    "created_at": session.get("created_at"),
                    "reference_label": session.get("reference_label"),
                    "recording_file": archive_name,
                    "mixed_file": mixed_name,
                    "analysis": session.get("analysis", {}),
                }
            )
        archive.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

    filename = f"coach-sessions-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return buffer.getvalue(), filename
