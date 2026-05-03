from __future__ import annotations

from typing import Any


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
        "received": {
            "mime_type": mime_type or "application/octet-stream",
            "bytes": len(audio_bytes),
            "size_kb": size_kb,
            "recorded_duration": round(duration, 2),
        },
    }
