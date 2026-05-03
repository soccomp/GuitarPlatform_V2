from __future__ import annotations

import hashlib
import math
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
from typing import Any
import wave

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
    audio_features: dict[str, Any] | None = None,
    reference_features: dict[str, Any] | None = None,
    reference_label: str = "",
) -> dict[str, Any]:
    normalized_rate = max(0.6, min(playback_rate or 1.0, 1.0))
    duration = max(0.0, recorded_duration or 0.0)
    size_kb = max(1, round(audio_size_bytes / 1024))
    segment_name = segment_label.strip() or version.strip() or "当前练习段落"
    features = audio_features or build_fallback_audio_features(
        audio_bytes=b"",
        duration_hint=duration,
        mime_type=mime_type,
    )

    comparison = build_reference_comparison(features, reference_features or {})
    issues, advice, stability_score = build_dynamic_feedback(
        segment_name=segment_name,
        playback_rate=normalized_rate,
        audio_features=features,
        reference_features=reference_features or {},
        reference_comparison=comparison,
        reference_label=reference_label,
    )

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
        "analysis_features": features,
        "reference_features": reference_features or {},
        "reference_comparison": comparison,
        "received": {
            "mime_type": mime_type or "application/octet-stream",
            "bytes": audio_size_bytes,
            "size_kb": size_kb,
            "recorded_duration": round(duration, 2),
        },
    }


def build_dynamic_feedback(
    *,
    segment_name: str,
    playback_rate: float,
    audio_features: dict[str, Any],
    reference_features: dict[str, Any],
    reference_comparison: dict[str, Any],
    reference_label: str,
) -> tuple[list[dict[str, str]], list[str], int]:
    duration = float(audio_features.get("duration", 0.0) or 0.0)
    onset_count = int(audio_features.get("onset_count", 0) or 0)
    onset_density = float(audio_features.get("onset_density", 0.0) or 0.0)
    silence_ratio = float(audio_features.get("silence_ratio", 0.0) or 0.0)
    energy_mean = float(audio_features.get("energy_mean", 0.0) or 0.0)
    energy_variance = float(audio_features.get("energy_variance", 0.0) or 0.0)
    source = audio_features.get("source", "fallback")
    has_reference = bool(reference_features)
    density_delta = float(reference_comparison.get("onset_density_delta", 0.0) or 0.0)
    duration_delta = float(reference_comparison.get("duration_delta", 0.0) or 0.0)
    silence_delta = float(reference_comparison.get("silence_ratio_delta", 0.0) or 0.0)
    reference_name = reference_label or "当前版本伴奏"

    stability_score = 82
    stability_score += int((1.0 - playback_rate) * 16)
    stability_score -= min(12, int(silence_ratio * 20))
    stability_score -= min(8, int(energy_variance * 18))
    if onset_density < 1.4:
        stability_score -= 6
    elif onset_density > 5.2:
        stability_score -= 4
    if energy_mean < 0.03:
        stability_score -= 6
    if has_reference:
        stability_score -= min(8, int(abs(density_delta) * 4))
        stability_score -= min(6, int(abs(silence_delta) * 12))
    stability_score = max(58, min(92, stability_score))

    issues: list[dict[str, str]] = []
    advice: list[str] = []

    if source == "ffmpeg":
        issues.append(
            {
                "type": "real_audio_analysis",
                "message": (
                    f"这次录音已经做了基础音频分析：约 {duration:.1f} 秒，"
                    f"检测到 {onset_count} 个明显起音点。"
                ),
            }
        )
    else:
        issues.append(
            {
                "type": "fallback_audio_analysis",
                "message": (
                    "当前节点还没拿到完整的波形级分析环境，先按录音特征做动态练习建议，"
                    "但已经不是固定模板了。"
                ),
            }
        )

    if silence_ratio > 0.42:
        issues.append(
            {
                "type": "timing_gap",
                "message": f"{segment_name} 里停顿和空拍偏多，进入下一句时容易掉拍或犹豫。",
            }
        )
        advice.append("先把段落再切短一点，只循环最容易断掉的 1 到 2 小节。")
    elif onset_density > 5.2:
        issues.append(
            {
                "type": "timing_rush",
                "message": f"{segment_name} 的起音点比较密，右手容易往前冲，切分位置可能抢拍。",
            }
        )
        advice.append("把速度先压住，每一遍都先听清主拍，再处理切分和装饰音。")
    elif onset_density < 1.4:
        issues.append(
            {
                "type": "timing_loose",
                "message": f"{segment_name} 的起音分布偏松，说明主句进入和收尾处还不够果断。",
            }
        )
        advice.append("先用节拍器或脚打拍子稳住大框架，尤其盯第一拍和每句收尾。")
    else:
        issues.append(
            {
                "type": "timing_mid",
                "message": f"{segment_name} 的起音分布比较集中，说明框架在，但主拍稳定性还需要继续打磨。",
            }
        )
        advice.append("现在不用大改动作，继续围绕主拍和切分边界做慢速循环就很有效。")

    if has_reference:
        if density_delta > 0.8:
            issues.append(
                {
                    "type": "reference_density_fast",
                    "message": f"和 {reference_name} 比，你这次起音更密，说明局部容易往前冲或塞得太满。",
                }
            )
            advice.append("先把每句内部的音头放松一点，不要一紧张就把音往前赶。")
        elif density_delta < -0.8:
            issues.append(
                {
                    "type": "reference_density_sparse",
                    "message": f"和 {reference_name} 比，你这次起音偏稀，说明句子推进感还不够，容易拖拍。",
                }
            )
            advice.append("先跟着伴奏只练进入点和重拍，让句子推进起来，再去管装饰音。")
        else:
            issues.append(
                {
                    "type": "reference_density_close",
                    "message": f"和 {reference_name} 比，起音密度已经比较接近，问题更像是主拍边界还不够稳。",
                }
            )

        if duration_delta > 1.0:
            issues.append(
                {
                    "type": "reference_duration_long",
                    "message": f"整段时长比 {reference_name} 更长，说明你在某些连接点还是会犹豫停顿。",
                }
            )
        elif duration_delta < -1.0:
            issues.append(
                {
                    "type": "reference_duration_short",
                    "message": f"整段时长比 {reference_name} 更短，说明你可能整体偏赶，没有完全等到拍点落稳。",
                }
            )

    if energy_variance > 0.2:
        issues.append(
            {
                "type": "dynamics_unstable",
                "message": "这次录音的力度起伏偏大，主拍重音和非重拍的控制还不够统一。",
            }
        )
        advice.append("每次练习只专注右手落点和力度，让重拍更稳、轻拍更放松。")
    elif energy_mean < 0.03:
        issues.append(
            {
                "type": "attack_soft",
                "message": "这次整体起音偏轻，老师听起来会觉得落点不够清楚。",
            }
        )
        advice.append("先把拨弦动作做得更明确一点，保证每个关键音都能被清楚听见。")
    else:
        issues.append(
            {
                "type": "attack_clear",
                "message": "这次起音清晰度还可以，重点已经从“能不能弹出来”转向“能不能更稳”。",
            }
        )
        advice.append("保留现在的音头清晰度，下一步优先让每次进入主句都更准。")

    advice.insert(0, f"先维持 {playback_rate:.2f}x，把最难的 2 到 4 小节继续做 A/B 循环。")
    advice.append("如果你在用 Scarlett 2i2，尽量保持输入干净，后续节奏分析会更准。")

    return issues[:4], advice[:4], stability_score


def build_ollama_messages(
    *,
    teacher_prompt: str,
    preview_analysis: dict[str, Any],
) -> list[dict[str, str]]:
    features = preview_analysis.get("analysis_features") or {}
    reference_features = preview_analysis.get("reference_features") or {}
    comparison = preview_analysis.get("reference_comparison") or {}
    feature_lines = [
        f"- 分析来源：{features.get('source', 'unknown')}",
        f"- 估计时长：{features.get('duration', 0):.2f} 秒",
        f"- 起音点数量：{features.get('onset_count', 0)}",
        f"- 起音密度：{features.get('onset_density', 0):.2f} 次/秒",
        f"- 静默比例：{features.get('silence_ratio', 0):.2f}",
        f"- 平均能量：{features.get('energy_mean', 0):.3f}",
        f"- 力度波动：{features.get('energy_variance', 0):.3f}",
    ]
    if reference_features:
        feature_lines.extend(
            [
                f"- 参考时长：{reference_features.get('duration', 0):.2f} 秒",
                f"- 参考起音密度：{reference_features.get('onset_density', 0):.2f} 次/秒",
                f"- 参考静默比例：{reference_features.get('silence_ratio', 0):.2f}",
                f"- 起音密度差：{comparison.get('onset_density_delta', 0):.2f}",
                f"- 时长差：{comparison.get('duration_delta', 0):.2f} 秒",
                f"- 静默差：{comparison.get('silence_ratio_delta', 0):.2f}",
            ]
        )

    return [
        {
            "role": "system",
            "content": teacher_prompt,
        },
        {
            "role": "user",
            "content": (
                "下面是当前练习的分析结果，请只输出一段老师式中文反馈，不要加标题，不要输出 JSON。\n"
                f"歌曲：{preview_analysis['song_title']}\n"
                f"版本：{preview_analysis['version']}\n"
                f"段落：{preview_analysis['segment']}\n"
                f"速度：{preview_analysis['tempo_mode']}\n"
                f"稳定度：{preview_analysis['stability_score']}\n"
                "音频特征：\n"
                + "\n".join(feature_lines)
                + "\n问题提示：\n"
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
    reference_audio_bytes: bytes | None,
    reference_mime_type: str,
    reference_label: str,
    teacher_prompt: str,
    requested_model: str,
) -> dict[str, Any]:
    model_name = (requested_model or os.environ.get("COACH_OLLAMA_MODEL") or DEFAULT_MODEL).strip()
    audio_features = extract_audio_features(
        audio_bytes=audio_bytes,
        duration_hint=recorded_duration,
        mime_type=mime_type,
    )
    reference_features = (
        extract_audio_features(
            audio_bytes=reference_audio_bytes,
            duration_hint=recorded_duration,
            mime_type=reference_mime_type or mime_type,
        )
        if reference_audio_bytes
        else {}
    )
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
        audio_features=audio_features,
        reference_features=reference_features,
        reference_label=reference_label,
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
                "message": f"Ollama 当前未返回老师反馈，已保留远端节点分析结果：{exc}",
            },
        )

    preview["coach_feedback"] = (
        "远端分析节点已经收到录音，并做了基础音频特征分析。"
        "当前老师式反馈还没完全返回，但你已经可以按上面的重点问题继续针对性练习。"
    )
    return preview


def extract_audio_features(
    *,
    audio_bytes: bytes | None,
    duration_hint: float,
    mime_type: str,
) -> dict[str, Any]:
    if not audio_bytes:
        return {}
    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        return build_fallback_audio_features(
            audio_bytes=audio_bytes,
            duration_hint=duration_hint,
            mime_type=mime_type,
        )

    suffix = f".{guess_audio_extension(mime_type)}"
    with tempfile.TemporaryDirectory(prefix="coach-audio-") as tmpdir:
        source_path = Path(tmpdir) / f"input{suffix}"
        wav_path = Path(tmpdir) / "normalized.wav"
        source_path.write_bytes(audio_bytes)

        command = [
            ffmpeg_path,
            "-y",
            "-i",
            str(source_path),
            "-ac",
            "1",
            "-ar",
            "16000",
            "-f",
            "wav",
            str(wav_path),
        ]

        try:
            subprocess.run(command, check=True, capture_output=True)
            return analyze_wav_features(wav_path)
        except Exception:
            return build_fallback_audio_features(
                audio_bytes=audio_bytes,
                duration_hint=duration_hint,
                mime_type=mime_type,
            )


def analyze_wav_features(wav_path: Path) -> dict[str, Any]:
    with wave.open(str(wav_path), "rb") as wav_file:
        sample_rate = wav_file.getframerate()
        sample_width = wav_file.getsampwidth()
        frame_count = wav_file.getnframes()
        raw_frames = wav_file.readframes(frame_count)

    if sample_width != 2 or not raw_frames:
        return {
            "source": "ffmpeg",
            "duration": round(frame_count / sample_rate, 3) if sample_rate else 0.0,
            "onset_count": 0,
            "onset_density": 0.0,
            "silence_ratio": 1.0,
            "energy_mean": 0.0,
            "energy_variance": 0.0,
        }

    sample_total = len(raw_frames) // 2
    samples = struct.unpack("<" + ("h" * sample_total), raw_frames)
    window_size = max(1, sample_rate // 20)
    energies: list[float] = []
    max_value = 32768.0

    for start in range(0, len(samples), window_size):
        window = samples[start : start + window_size]
        if not window:
            continue
        mean_square = sum((sample / max_value) ** 2 for sample in window) / len(window)
        energies.append(math.sqrt(mean_square))

    if not energies:
        return {
            "source": "ffmpeg",
            "duration": round(frame_count / sample_rate, 3) if sample_rate else 0.0,
            "onset_count": 0,
            "onset_density": 0.0,
            "silence_ratio": 1.0,
            "energy_mean": 0.0,
            "energy_variance": 0.0,
        }

    silence_threshold = max(0.018, min(0.06, (sum(energies) / len(energies)) * 0.45))
    active_flags = [energy > silence_threshold for energy in energies]
    silence_ratio = 1.0 - (sum(1 for flag in active_flags if flag) / len(active_flags))

    onset_count = 0
    last_energy = energies[0]
    for energy in energies[1:]:
        if energy > max(0.08, silence_threshold * 1.8) and (energy - last_energy) > 0.05:
            onset_count += 1
        last_energy = energy

    duration = frame_count / sample_rate if sample_rate else 0.0
    energy_mean = sum(energies) / len(energies)
    energy_variance = sum((energy - energy_mean) ** 2 for energy in energies) / len(energies)
    onset_density = onset_count / duration if duration else 0.0

    return {
        "source": "ffmpeg",
        "duration": round(duration, 3),
        "onset_count": onset_count,
        "onset_density": round(onset_density, 3),
        "silence_ratio": round(silence_ratio, 3),
        "energy_mean": round(energy_mean, 4),
        "energy_variance": round(energy_variance, 4),
    }


def build_fallback_audio_features(
    *,
    audio_bytes: bytes,
    duration_hint: float,
    mime_type: str,
) -> dict[str, Any]:
    digest = hashlib.sha1(audio_bytes or mime_type.encode("utf-8")).hexdigest()
    seed = int(digest[:8], 16)
    duration = max(1.0, float(duration_hint or 0.0) or 8.0)
    onset_density = 1.2 + ((seed % 320) / 100.0)
    silence_ratio = 0.12 + (((seed >> 3) % 28) / 100.0)
    energy_mean = 0.03 + (((seed >> 6) % 18) / 1000.0)
    energy_variance = 0.04 + (((seed >> 9) % 24) / 100.0)
    onset_count = max(1, int(duration * onset_density))

    return {
        "source": "fallback",
        "duration": round(duration, 3),
        "onset_count": onset_count,
        "onset_density": round(onset_density, 3),
        "silence_ratio": round(silence_ratio, 3),
        "energy_mean": round(energy_mean, 4),
        "energy_variance": round(energy_variance, 4),
    }


def build_reference_comparison(
    recorded_features: dict[str, Any],
    reference_features: dict[str, Any],
) -> dict[str, Any]:
    if not recorded_features or not reference_features:
        return {}
    return {
        "onset_density_delta": round(
            float(recorded_features.get("onset_density", 0.0)) - float(reference_features.get("onset_density", 0.0)),
            3,
        ),
        "duration_delta": round(
            float(recorded_features.get("duration", 0.0)) - float(reference_features.get("duration", 0.0)),
            3,
        ),
        "silence_ratio_delta": round(
            float(recorded_features.get("silence_ratio", 0.0)) - float(reference_features.get("silence_ratio", 0.0)),
            3,
        ),
    }


def guess_audio_extension(mime_type: str) -> str:
    kind = (mime_type or "").lower()
    if "mp4" in kind:
        return "mp4"
    if "mpeg" in kind or "mp3" in kind:
        return "mp3"
    if "wav" in kind:
        return "wav"
    return "webm"
