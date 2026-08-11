import mimetypes
from urllib.parse import quote

from fastapi import APIRouter, Body, File, Form, HTTPException, Query, Request, Response, UploadFile

from services.coach import analyze_practice_audio
from services.coach import get_coach_runtime_status
from services.coach_sessions import (
    create_session,
    delete_sessions,
    export_sessions_zip,
    find_session,
    list_sessions,
    resolve_mixed_path,
    resolve_recording_path,
)
from services.index_store import find_song, load_index, resolve_under
from services.learning_recommendations import build_song_learning_recommendations
from config import SONGS_DIR
from services.media_response import media_file_response


router = APIRouter(prefix="/api/coach", tags=["coach"])


def build_session_response(session: dict) -> dict:
    result = dict(session.get("analysis") or {})
    result.setdefault("song_title", session.get("song_title", ""))
    result.setdefault("version", session.get("version", ""))
    result.setdefault("segment", session.get("segment", ""))
    result["session_id"] = session.get("id")
    result["recording_url"] = f"/api/coach/sessions/{session['id']}/recording"
    result["mix_url"] = f"/api/coach/sessions/{session['id']}/mix" if session.get("mixed_path") else ""
    result["recording_kind"] = session.get("recording_kind", "audio")
    result["mixed_kind"] = session.get("mixed_kind", "")
    result["recording_mime_type"] = session.get("recording_mime_type", "audio/webm")
    result["mixed_mime_type"] = session.get("mixed_mime_type", "")
    result["reference_url"] = (
        f"/api/songs/{quote(session['song_id'])}/asset?path={quote(session['reference_asset_path'])}"
        if session.get("song_id") and session.get("reference_asset_path")
        else ""
    )
    result["created_at"] = session.get("created_at", "")
    result["coach_model"] = session.get("coach_model", "")
    result["recording_duration"] = session.get("recording_duration", 0.0)
    return result


@router.post("/analyze-rhythm")
async def analyze_rhythm(
    song_id: str = Form(...),
    song_title: str = Form(...),
    version: str = Form(...),
    playback_rate: float = Form(1.0),
    segment_label: str = Form(""),
    recorded_duration: float = Form(0.0),
    reference_start_seconds: float = Form(0.0),
    sync_offset_seconds: float = Form(0.0),
    coach_model: str = Form(""),
    capture_mode: str = Form("audio"),
    reference_asset_path: str = Form(""),
    mix_media: UploadFile | None = File(None),
    media: UploadFile | None = File(None),
    audio: UploadFile | None = File(None),
):
    upload = media or audio
    if upload is None:
        raise HTTPException(status_code=400, detail="未收到录音或录像文件")

    audio_bytes = await upload.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="未收到录音文件")

    mixed_bytes = b""
    mixed_content_type = ""
    if mix_media is not None:
        mixed_bytes = await mix_media.read()
        mixed_content_type = mix_media.content_type or ""

    reference_audio_bytes = None
    reference_mime_type = ""
    reference_label = ""
    reference_path = None

    song = find_song(load_index(), song_id)
    if song:
        version_data = next((item for item in song.get("versions", []) if item.get("name") == version), None)
        audio_file = reference_asset_path or (version_data or {}).get("files", {}).get("audio")
        if audio_file:
            try:
                reference_path = resolve_under(SONGS_DIR, f"{song['path']}/{audio_file}")
                if reference_path.exists():
                    reference_audio_bytes = reference_path.read_bytes()
                    reference_mime_type = mimetypes.guess_type(reference_path.name)[0] or ""
                    reference_label = audio_file
            except ValueError:
                reference_audio_bytes = None
                reference_path = None

    result = await analyze_practice_audio(
        song_id=song_id,
        song_title=song_title,
        version=version,
        playback_rate=playback_rate,
        audio_bytes=audio_bytes,
        mime_type=upload.content_type or "",
        segment_label=segment_label,
        recorded_duration=recorded_duration,
        reference_audio_bytes=reference_audio_bytes,
        reference_mime_type=reference_mime_type,
        reference_label=reference_label,
        coach_model=coach_model,
    )

    extension = "webm"
    content_type = upload.content_type or ""
    if "mp4" in content_type:
        extension = "mp4"
    elif "mpeg" in content_type or "mp3" in content_type:
        extension = "mp3"
    elif "ogg" in content_type:
        extension = "ogg"

    mixed_extension = ""
    if mixed_content_type:
        if "mp4" in mixed_content_type:
            mixed_extension = "mp4"
        elif "mpeg" in mixed_content_type or "mp3" in mixed_content_type:
            mixed_extension = "mp3"
        elif "ogg" in mixed_content_type:
            mixed_extension = "ogg"
        else:
            mixed_extension = "webm"

    session = create_session(
        song_id=song_id,
        song_title=song_title,
        version=version,
        segment_label=segment_label or version,
        coach_model=coach_model or result.get("model") or "",
        recording_bytes=audio_bytes,
        recording_extension=extension,
        recording_mime_type=content_type or "audio/webm",
        recording_kind="video" if capture_mode == "video" else "audio",
        mixed_bytes=mixed_bytes or None,
        mixed_extension=mixed_extension,
        mixed_mime_type=mixed_content_type,
        recorded_duration=recorded_duration,
        playback_rate=playback_rate,
        reference_start_seconds=reference_start_seconds,
        sync_offset_seconds=sync_offset_seconds,
        reference_label=reference_label,
        reference_asset_path=(audio_file or "") if song else "",
        reference_source_path=reference_path if song and audio_file else None,
        analysis_result=result,
    )
    return build_session_response(session)


@router.get("/sessions")
async def get_sessions():
    return [build_session_response(session) for session in list_sessions()]


@router.get("/status")
async def get_coach_status():
    return await get_coach_runtime_status()


@router.get("/recommendations")
async def get_learning_recommendations(song_id: str = Query(..., description="当前歌曲 id")):
    index = load_index()
    song = find_song(index, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return build_song_learning_recommendations(song, index)


@router.get("/sessions/{session_id}/recording")
async def stream_session_recording(session_id: str, request: Request):
    session = find_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")

    try:
        recording_path = resolve_recording_path(session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not recording_path.exists():
        raise HTTPException(status_code=404, detail="Recording file not found")

    return media_file_response(recording_path, request)


@router.get("/sessions/{session_id}/mix")
async def stream_session_mix(session_id: str, request: Request):
    session = find_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")
    if not session.get("mixed_path"):
        raise HTTPException(status_code=404, detail="Mixed practice file not found")

    try:
        mixed_path = resolve_mixed_path(session)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not mixed_path.exists():
        raise HTTPException(status_code=404, detail="Mixed practice file not found")

    return media_file_response(mixed_path, request)


@router.delete("/sessions")
async def remove_sessions(session_ids: list[str] = Body(..., embed=True)):
    result = delete_sessions(session_ids)
    result["sessions"] = [build_session_response(session) for session in result["sessions"]]
    return result


@router.get("/sessions/export")
async def export_sessions(ids: str = Query(..., description="Comma-separated session ids")):
    session_ids = [item.strip() for item in ids.split(",") if item.strip()]
    content, filename = export_sessions_zip(session_ids)
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return Response(content=content, media_type="application/zip", headers=headers)
