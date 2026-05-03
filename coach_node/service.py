from __future__ import annotations

import os
from typing import Any

import httpx


DEFAULT_OLLAMA_BASE_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3:8b"


def build_node_preview_analysis(
    *,
    song_id: str,
    song_title: str,
    version: str,
    segment_label: str,
    playback_rate: float,
    recorded_duration: float,
    mime_type: str,
    audio_size_bytes: int,
    model_name: str,
) -> dict[str, Any]:
    normalized_rate = max(0.6, min(playback_rate or 1.0, 1.0))
    duration = max(0.0, recorded_duration or 0.0)
    size_kb = max(1, round(audio_size_bytes / 1024))
    stability_score = max(66, min(90, 76 + int((1.0 - normalized_rate) * 18) - (6 if duration < 8 else 0)))
    segment_name = segment_label.strip() or version.strip() or "当前练习段落"

    issues = [
        {
            "type": "segment_entry",
            "message": f"{segment_name} 的主句进入点值得重点盯一下，先确认每次第一拍是否都落稳。",
        },
        {
            "type": "timing_consistency",
            "message": "这一版远端节点已经收到录音，但节奏对齐算法还没接入，当前先用练习策略级反馈占位。",
        },
    ]
    advice = [
        f"先维持 {normalized_rate:.2f}x，把最难的 2 到 4 小节做 A/B 循环。",
        "每次只盯一个问题：先稳主拍，再看切分和进入点。",
        "如果你在用 Scarlett 2i2，尽量让吉他输入干净一点，后面节奏分析会更准。",
    ]

    return {
        "mode": "remote_node_preview",
        "provider": "ollama",
        "model": model_name,
        "song_id": song_id,
        "song_title": song_title,
        "version": version,
        "segment": segment_name,
        "tempo_mode": f"{normalized_rate:.2f}x",
        "stability_score": stability_score,
        "issues": issues,
        "advice": advice,
        "coach_feedback": "",
        "received": {
            "mime_type": mime_type or "application/octet-stream",
            "bytes": audio_size_bytes,
            "size_kb": size_kb,
            "recorded_duration": round(duration, 2),
        },
    }


def build_ollama_messages(
    *,
    teacher_prompt: str,
    preview_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": teacher_prompt,
        },
        {
            "role": "user",
            "content": (
                "下面是当前练习的预分析结果，请只输出一段老师式中文反馈，不要加标题，不要输出 JSON。\n"
                f"歌曲：{preview_analysis['song_title']}\n"
                f"版本：{preview_analysis['version']}\n"
                f"段落：{preview_analysis['segment']}\n"
                f"速度：{preview_analysis['tempo_mode']}\n"
                f"稳定度：{preview_analysis['stability_score']}\n"
                "问题提示：\n"
                + "\n".join(f"- {item['message']}" for item in preview_analysis["issues"])
                + "\n练习建议：\n"
                + "\n".join(f"- {item}" for item in preview_analysis["advice"])
            ),
        },
    ]


async def request_ollama_feedback(
    *,
    model_name: str,
    teacher_prompt: str,
    preview_analysis: dict[str, Any],
) -> str:
    base_url = os.environ.get("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).rstrip("/")
    payload = {
        "model": model_name or DEFAULT_MODEL,
        "messages": build_ollama_messages(
            teacher_prompt=teacher_prompt,
            preview_analysis=preview_analysis,
        ),
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(f"{base_url}/api/chat", json=payload)
    response.raise_for_status()
    return extract_ollama_message(response.json())


def extract_ollama_message(payload: dict[str, Any]) -> str:
    message = payload.get("message") or {}
    content = message.get("content") or ""
    return str(content).strip()


async def analyze_with_ollama(
    *,
    song_id: str,
    song_title: str,
    version: str,
    segment_label: str,
    playback_rate: float,
    recorded_duration: float,
    mime_type: str,
    audio_bytes: bytes,
    teacher_prompt: str,
    requested_model: str,
) -> dict[str, Any]:
    model_name = (requested_model or os.environ.get("COACH_OLLAMA_MODEL") or DEFAULT_MODEL).strip()
    preview = build_node_preview_analysis(
        song_id=song_id,
        song_title=song_title,
        version=version,
        segment_label=segment_label,
        playback_rate=playback_rate,
        recorded_duration=recorded_duration,
        mime_type=mime_type,
        audio_size_bytes=len(audio_bytes),
        model_name=model_name,
    )
    try:
        preview["coach_feedback"] = await request_ollama_feedback(
            model_name=model_name,
            teacher_prompt=teacher_prompt,
            preview_analysis=preview,
        )
        if preview["coach_feedback"]:
            preview["mode"] = "remote_node"
            return preview
    except Exception as exc:
        preview["issues"].insert(
            0,
            {
                "type": "ollama_unavailable",
                "message": f"Ollama 当前未返回老师反馈，已保留远端节点占位分析：{exc}",
            },
        )

    preview["coach_feedback"] = (
        "远端分析节点已经收到录音，但当前还在等待 Ollama 模型完成老师式反馈。"
        "你可以先按上面的建议继续慢速分段练，等模型可用后，这里会返回更自然的中文点评。"
    )
    return preview
