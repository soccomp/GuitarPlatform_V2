from __future__ import annotations

import io
import json
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
    normalized.setdefault("recording_mime_type", "audio/webm")
    normalized.setdefault("recording_duration", 0.0)
    normalized.setdefault("reference_label", "")
    normalized.setdefault("reference_asset_path", "")
    normalized.setdefault("created_at", "")
    normalized.setdefault("analysis", {})
    normalized["recording_path"] = clean_relative_path(normalized.get("recording_path", ""))
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
    recorded_duration: float,
    reference_label: str,
    reference_asset_path: str,
    analysis_result: dict,
) -> dict:
    session_id = uuid.uuid4().hex[:12]
    timestamp = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    relative_dir = Path(song_id or "unknown-song") / session_id
    relative_recording_path = relative_dir / f"practice-take.{recording_extension}"
    absolute_recording_path = COACH_RECORDINGS_DIR / relative_recording_path
    absolute_recording_path.parent.mkdir(parents=True, exist_ok=True)
    absolute_recording_path.write_bytes(recording_bytes)

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
            "recording_mime_type": recording_mime_type,
            "recording_duration": recorded_duration,
            "reference_label": reference_label,
            "reference_asset_path": reference_asset_path,
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
    candidate = (COACH_RECORDINGS_DIR / clean_relative_path(session.get("recording_path", ""))).resolve()
    base = COACH_RECORDINGS_DIR.resolve()
    if candidate != base and base not in candidate.parents:
        raise ValueError("Recording path escapes base directory")
    return candidate


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
            if recording_path.exists():
                recording_path.unlink()
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
                    "analysis": session.get("analysis", {}),
                }
            )
        archive.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False, indent=2))

    filename = f"coach-sessions-{datetime.now().strftime('%Y%m%d-%H%M%S')}.zip"
    return buffer.getvalue(), filename
