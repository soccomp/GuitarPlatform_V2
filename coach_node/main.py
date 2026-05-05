from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from service import analyze_with_ollama, build_content_intelligence_with_ollama


app = FastAPI(title="Guitar Coach Node")


class ContentIntelligenceRequest(BaseModel):
    content_type: str
    title: str
    subtitle: str = ""
    description: str = ""
    tags: list[str] = []
    transcript_preview: str = ""
    transcript_text: str = ""
    coach_model: str = "qwen3:8b"
    system_prompt: str = ""


@app.get("/health")
async def health():
    return {"ok": True, "service": "guitar-coach-node"}


@app.post("/api/coach/analyze-rhythm")
async def analyze_rhythm(
    song_id: str = Form(...),
    song_title: str = Form(...),
    version: str = Form(...),
    playback_rate: float = Form(1.0),
    segment_label: str = Form(""),
    recorded_duration: float = Form(0.0),
    reference_label: str = Form(""),
    coach_model: str = Form("qwen3:8b"),
    teacher_prompt: str = Form(...),
    audio: UploadFile = File(...),
    reference_audio: UploadFile | None = File(None),
):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="未收到录音文件")
    reference_audio_bytes = await reference_audio.read() if reference_audio else None

    return await analyze_with_ollama(
        song_id=song_id,
        song_title=song_title,
        version=version,
        segment_label=segment_label,
        playback_rate=playback_rate,
        recorded_duration=recorded_duration,
        mime_type=audio.content_type or "",
        audio_bytes=audio_bytes,
        reference_audio_bytes=reference_audio_bytes,
        reference_mime_type=reference_audio.content_type if reference_audio else "",
        reference_label=reference_label,
        teacher_prompt=teacher_prompt,
        requested_model=coach_model,
    )


@app.post("/api/coach/content-intelligence")
async def build_content_intelligence(body: ContentIntelligenceRequest):
    return await build_content_intelligence_with_ollama(
        content_type=body.content_type,
        title=body.title,
        subtitle=body.subtitle,
        description=body.description,
        tags=body.tags,
        transcript_preview=body.transcript_preview,
        transcript_text=body.transcript_text,
        requested_model=body.coach_model,
        system_prompt=body.system_prompt,
    )
