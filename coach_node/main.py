from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from service import analyze_with_ollama


app = FastAPI(title="Guitar Coach Node")


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
    coach_model: str = Form("qwen3:8b"),
    teacher_prompt: str = Form(...),
    audio: UploadFile = File(...),
):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="未收到录音文件")

    return await analyze_with_ollama(
        song_id=song_id,
        song_title=song_title,
        version=version,
        segment_label=segment_label,
        playback_rate=playback_rate,
        recorded_duration=recorded_duration,
        mime_type=audio.content_type or "",
        audio_bytes=audio_bytes,
        teacher_prompt=teacher_prompt,
        requested_model=coach_model,
    )
