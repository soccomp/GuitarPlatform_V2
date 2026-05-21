import os

import httpx
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from service import analyze_with_ollama, build_content_intelligence_with_ollama


app = FastAPI(title="Guitar Coach Node")
DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:8b"


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


def get_ollama_base_url() -> str:
    return (os.environ.get("OLLAMA_BASE_URL") or DEFAULT_OLLAMA_BASE_URL).strip()


def get_default_model() -> str:
    return (os.environ.get("COACH_OLLAMA_MODEL") or DEFAULT_MODEL).strip()


def humanize_model_name(model_name: str) -> str:
    normalized = (model_name or "").strip()
    lower = normalized.lower()
    if lower == "qwen3:8b":
        return "Qwen 3 8B"
    if lower == "deepseek-r1:8b":
        return "DeepSeek R1 8B"
    if ":" in normalized:
        base, size = normalized.split(":", 1)
        return f"{base} {size}".strip()
    return normalized or "未命名模型"


def normalize_model_entries(raw_items: list[dict] | list[str] | None) -> list[dict[str, str]]:
    items = raw_items or []
    normalized: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in items:
        name = ""
        if isinstance(item, dict):
            name = str(item.get("name") or item.get("model") or "").strip()
        else:
            name = str(item or "").strip()
        if not name or name in seen:
            continue
        seen.add(name)
        normalized.append(
            {
                "value": name,
                "label": humanize_model_name(name),
            }
        )
    return normalized


async def fetch_ollama_json(path: str) -> dict:
    base_url = get_ollama_base_url().rstrip("/")
    timeout = httpx.Timeout(4.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(f"{base_url}{path}")
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Ollama 返回格式无效")
    return payload


@app.get("/health")
async def health():
    default_model = get_default_model()
    installed_models: list[dict[str, str]] = []
    running_models: list[dict[str, str]] = []
    ollama_connected = False
    ollama_error = ""
    try:
        tags_payload = await fetch_ollama_json("/api/tags")
        ps_payload = await fetch_ollama_json("/api/ps")
        installed_models = normalize_model_entries(tags_payload.get("models"))
        running_models = normalize_model_entries(ps_payload.get("models"))
        ollama_connected = True
    except Exception as exc:
        ollama_error = str(exc)

    return {
        "ok": True,
        "service": "guitar-coach-node",
        "ollama_base_url": get_ollama_base_url(),
        "ollama_connected": ollama_connected,
        "ollama_error": ollama_error,
        "default_model": default_model,
        "installed_models": installed_models,
        "running_models": running_models,
    }


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
