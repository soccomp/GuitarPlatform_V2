import mimetypes

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.coach import analyze_practice_audio
from services.index_store import find_song, load_index, resolve_under
from config import SONGS_DIR


router = APIRouter(prefix="/api/coach", tags=["coach"])


@router.post("/analyze-rhythm")
async def analyze_rhythm(
    song_id: str = Form(...),
    song_title: str = Form(...),
    version: str = Form(...),
    playback_rate: float = Form(1.0),
    segment_label: str = Form(""),
    recorded_duration: float = Form(0.0),
    audio: UploadFile = File(...),
):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="未收到录音文件")

    reference_audio_bytes = None
    reference_mime_type = ""
    reference_label = ""

    song = find_song(load_index(), song_id)
    if song:
        version_data = next((item for item in song.get("versions", []) if item.get("name") == version), None)
        audio_file = (version_data or {}).get("files", {}).get("audio")
        if audio_file:
            try:
                reference_path = resolve_under(SONGS_DIR, f"{song['path']}/{audio_file}")
                if reference_path.exists():
                    reference_audio_bytes = reference_path.read_bytes()
                    reference_mime_type = mimetypes.guess_type(reference_path.name)[0] or ""
                    reference_label = audio_file
            except ValueError:
                reference_audio_bytes = None

    return await analyze_practice_audio(
        song_id=song_id,
        song_title=song_title,
        version=version,
        playback_rate=playback_rate,
        audio_bytes=audio_bytes,
        mime_type=audio.content_type or "",
        segment_label=segment_label,
        recorded_duration=recorded_duration,
        reference_audio_bytes=reference_audio_bytes,
        reference_mime_type=reference_mime_type,
        reference_label=reference_label,
    )
