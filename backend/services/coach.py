from __future__ import annotations

from typing import Any
import os

import httpx

from services.ai_assistant import ENV_FILES, read_env_value


DEFAULT_COACH_NODE_TIMEOUT_SECONDS = 90.0


class CoachNodeError(RuntimeError):
    pass


async def analyze_practice_audio(
    *,
    song_id: str,
    song_title: str,
    version: str,
    playback_rate: float,
    audio_bytes: bytes,
    mime_type: str,
    segment_label: str = "",
    recorded_duration: float = 0.0,
    reference_audio_bytes: bytes | None = None,
    reference_mime_type: str = "",
    reference_label: str = "",
) -> dict[str, Any]:
    if get_coach_node_url():
        try:
            return await send_to_coach_node(
                song_id=song_id,
                song_title=song_title,
                version=version,
                playback_rate=playback_rate,
                audio_bytes=audio_bytes,
                mime_type=mime_type,
                segment_label=segment_label,
                recorded_duration=recorded_duration,
                reference_audio_bytes=reference_audio_bytes,
                reference_mime_type=reference_mime_type,
                reference_label=reference_label,
            )
        except Exception as exc:
            preview = build_preview_rhythm_analysis(
                song_id=song_id,
                song_title=song_title,
                version=version,
                playback_rate=playback_rate,
                audio_bytes=audio_bytes,
                mime_type=mime_type,
                segment_label=segment_label,
                recorded_duration=recorded_duration,
            )
            preview["mode"] = "local_preview_fallback"
            preview["issues"].insert(
                0,
                {
                    "type": "coach_node_unavailable",
                    "message": f"4080 分析节点暂时不可用，已回退到本地预览反馈：{exc}",
                },
            )
            return preview

    return build_preview_rhythm_analysis(
        song_id=song_id,
        song_title=song_title,
        version=version,
        playback_rate=playback_rate,
        audio_bytes=audio_bytes,
        mime_type=mime_type,
        segment_label=segment_label,
        recorded_duration=recorded_duration,
    )


async def send_to_coach_node(
    *,
    song_id: str,
    song_title: str,
    version: str,
    playback_rate: float,
    audio_bytes: bytes,
    mime_type: str,
    segment_label: str = "",
    recorded_duration: float = 0.0,
    reference_audio_bytes: bytes | None = None,
    reference_mime_type: str = "",
    reference_label: str = "",
) -> dict[str, Any]:
    coach_node_url = get_coach_node_url()
    if not coach_node_url:
        raise CoachNodeError("未配置 COACH_NODE_URL")

    files = {
        "audio": (
            f"practice-take.{guess_audio_extension(mime_type)}",
            audio_bytes,
            mime_type or "application/octet-stream",
        ),
    }
    if reference_audio_bytes:
        files["reference_audio"] = (
            f"reference-track.{guess_audio_extension(reference_mime_type or mime_type)}",
            reference_audio_bytes,
            reference_mime_type or "application/octet-stream",
        )
    data = {
        "song_id": song_id,
        "song_title": song_title,
        "version": version,
        "segment_label": segment_label,
        "playback_rate": str(playback_rate),
        "recorded_duration": str(recorded_duration),
        "reference_label": reference_label,
        "coach_model": get_coach_model(),
        "teacher_prompt": build_teacher_feedback_prompt(
            song_title=song_title,
            version=version,
            segment_label=segment_label,
            playback_rate=playback_rate,
            recorded_duration=recorded_duration,
        ),
    }

    timeout = httpx.Timeout(get_coach_node_timeout_seconds())
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(coach_node_url, data=data, files=files)

    if response.status_code >= 400:
        raise CoachNodeError(f"分析节点返回错误：{response.status_code}")

    result = response.json()
    if not isinstance(result, dict):
        raise CoachNodeError("分析节点返回的数据格式无效")
    return result


def build_teacher_feedback_prompt(
    *,
    song_title: str,
    version: str,
    segment_label: str,
    playback_rate: float,
    recorded_duration: float,
) -> str:
    segment_name = segment_label.strip() or version.strip() or "当前练习段落"
    return (
        "你是一位经验丰富、语气自然的电吉他陪练老师。\n"
        "请根据节奏分析结果，用中文输出贴近真人教学的反馈。\n"
        "要求：\n"
        "1. 先指出最关键的 1 到 2 个问题，不要泛泛而谈。\n"
        "2. 明确告诉用户下一步该怎么练，例如继续降速、只循环哪几小节、先稳主拍再提速。\n"
        "3. 不要只给数字，要把数字解释成真正的练习建议。\n"
        "4. 语气专业、直接、鼓励，但不要空泛鼓励。\n"
        f"当前歌曲：{song_title}\n"
        f"当前版本：{version}\n"
        f"当前段落：{segment_name}\n"
        f"当前练习速度：{max(0.6, min(playback_rate or 1.0, 1.0)):.2f}x\n"
        f"当前录音时长：{max(0.0, recorded_duration or 0.0):.1f} 秒\n"
        "请把最终输出控制在 120 到 220 字之间。"
    )


def build_preview_rhythm_analysis(
    *,
    song_id: str,
    song_title: str,
    version: str,
    playback_rate: float,
    audio_bytes: bytes,
    mime_type: str,
    segment_label: str = "",
    recorded_duration: float = 0.0,
) -> dict[str, Any]:
    """Return a structured preview analysis until the 4080 coach node is connected."""

    normalized_rate = max(0.6, min(playback_rate or 1.0, 1.0))
    duration = max(0.0, recorded_duration or 0.0)
    size_kb = max(1, round(len(audio_bytes) / 1024))
    rate_bonus = int((1.0 - normalized_rate) * 20)
    duration_penalty = 6 if duration and duration < 8 else 0
    stability_score = max(62, min(88, 74 + rate_bonus - duration_penalty))

    segment_name = segment_label.strip() or version.strip() or "当前练习段落"
    lead_issue = (
        f"{segment_name} 已收到录音，当前先给出节奏练习预览反馈。"
        if duration
        else f"{segment_name} 已收到练习录音，等待下一阶段接入 4080 分析节点。"
    )
    entry_issue = "建议先确认每次进入主句的第一拍落点，再决定是否提速。"

    advice = [
        f"当前速度先维持在 {normalized_rate:.2f}x，连续练 3 到 5 遍再观察稳定性。",
        "优先用 A/B 循环锁定最难的两到四小节，不要整段反复刷。",
        "如果使用 Scarlett 2i2，尽量把吉他演奏音频和外放伴奏分开，后续分析会更准。",
    ]

    if duration and duration < 12:
        advice[0] = f"这次录音只有 {duration:.1f} 秒，建议下一遍至少完整弹过一个练习段落。"

    return {
        "mode": "local_preview",
        "song_id": song_id,
        "song_title": song_title,
        "version": version,
        "segment": segment_name,
        "tempo_mode": f"{normalized_rate:.2f}x",
        "stability_score": stability_score,
        "issues": [
            {
                "type": "preview_capture",
                "message": lead_issue,
            },
            {
                "type": "entry_timing",
                "message": entry_issue,
            },
        ],
        "advice": advice,
        "coach_feedback": (
            "这一版已经把录音、上传和结构化反馈链路接通了。"
            "现在返回的是本地预览反馈，等 4080 分析节点接上后，这里会升级成真正基于演奏音频的节奏诊断。"
        ),
        "teacher_prompt_preview": build_teacher_feedback_prompt(
            song_title=song_title,
            version=version,
            segment_label=segment_name,
            playback_rate=normalized_rate,
            recorded_duration=duration,
        ),
        "received": {
            "mime_type": mime_type or "application/octet-stream",
            "bytes": len(audio_bytes),
            "size_kb": size_kb,
            "recorded_duration": round(duration, 2),
        },
    }


def get_coach_node_url() -> str:
    configured = os.environ.get("COACH_NODE_URL", "").strip()
    if configured:
        return configured
    for env_file in ENV_FILES:
        configured = read_env_value(env_file, "COACH_NODE_URL")
        if configured:
            return configured
    return ""


def get_coach_model() -> str:
    configured = os.environ.get("COACH_MODEL", "").strip()
    if configured:
        return configured
    for env_file in ENV_FILES:
        configured = read_env_value(env_file, "COACH_MODEL")
        if configured:
            return configured
    return "qwen3:8b"


def get_coach_node_timeout_seconds() -> float:
    configured = os.environ.get("COACH_NODE_TIMEOUT_SECONDS", "").strip()
    if not configured:
        for env_file in ENV_FILES:
            configured = read_env_value(env_file, "COACH_NODE_TIMEOUT_SECONDS")
            if configured:
                break
    try:
        return float(configured) if configured else DEFAULT_COACH_NODE_TIMEOUT_SECONDS
    except ValueError:
        return DEFAULT_COACH_NODE_TIMEOUT_SECONDS


def guess_audio_extension(mime_type: str) -> str:
    kind = (mime_type or "").lower()
    if "mp4" in kind:
        return "mp4"
    if "mpeg" in kind or "mp3" in kind:
        return "mp3"
    if "wav" in kind:
        return "wav"
    return "webm"
