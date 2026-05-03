from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from services.coach import build_preview_rhythm_analysis


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

    return build_preview_rhythm_analysis(
        song_id=song_id,
        song_title=song_title,
        version=version,
        playback_rate=playback_rate,
        audio_bytes=audio_bytes,
        mime_type=audio.content_type or "",
        segment_label=segment_label,
        recorded_duration=recorded_duration,
    )
