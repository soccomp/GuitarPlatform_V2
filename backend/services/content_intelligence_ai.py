from __future__ import annotations

import json
from typing import Any

import httpx

from services.coach import CoachNodeError, get_coach_model, get_coach_node_timeout_seconds, get_coach_node_url


CONTENT_INTELLIGENCE_PROMPT = (
    "你是一个吉他学习平台的内容整理助手。"
    "请把输入内容整理成结构化学习画像，并且只输出 JSON。"
    "JSON 字段必须包含：summary, learning_focus, recommended_for, key_points, tags。"
    "summary 用 1 到 2 句中文说明内容讲什么，并点出最值得练的维度；"
    "learning_focus 用短语概括核心训练点；"
    "recommended_for 说明适合在什么练习问题下回看；"
    "key_points 最多 3 条，每条都是完整中文句子；"
    "tags 提供 4 到 8 个短标签。"
    "优先使用这些平台内统一标签：节奏、拨弦、Solo、乐理、指板、和弦、表达；"
    "如果内容不够，不要编造；"
    "输出必须是合法 JSON，不要带 markdown 代码块。"
)


async def build_ai_content_intelligence(
    *,
    content_type: str,
    title: str,
    subtitle: str,
    description: str,
    tags: list[str],
    transcript_preview: str,
    transcript_text: str,
    coach_model: str = "",
) -> dict[str, Any]:
    coach_node_url = get_coach_node_url()
    if not coach_node_url:
        raise CoachNodeError("未配置 COACH_NODE_URL，无法调用 4080 内容整理。")

    intelligence_url = coach_node_url.rsplit("/", 1)[0] + "/content-intelligence"
    payload = {
        "content_type": content_type,
        "title": title,
        "subtitle": subtitle,
        "description": description,
        "tags": tags,
        "transcript_preview": transcript_preview,
        "transcript_text": transcript_text[:6000],
        "coach_model": coach_model or get_coach_model(),
        "system_prompt": CONTENT_INTELLIGENCE_PROMPT,
    }

    timeout = httpx.Timeout(get_coach_node_timeout_seconds())
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(intelligence_url, json=payload)

    if response.status_code >= 400:
        raise CoachNodeError(f"内容整理节点返回错误：{response.status_code}")

    data = response.json()
    if not isinstance(data, dict):
        raise CoachNodeError("内容整理节点返回格式无效")
    return normalize_content_intelligence(data)


def normalize_content_intelligence(payload: dict[str, Any]) -> dict[str, Any]:
    raw = payload.get("intelligence", payload)
    if isinstance(raw, str):
        raw = _parse_json_text(raw)

    if not isinstance(raw, dict):
        raise CoachNodeError("内容整理节点未返回有效 JSON")

    key_points = raw.get("key_points") or []
    if not isinstance(key_points, list):
        key_points = []
    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []

    return {
        "summary": str(raw.get("summary", "")).strip(),
        "learning_focus": str(raw.get("learning_focus", "")).strip(),
        "recommended_for": str(raw.get("recommended_for", "")).strip(),
        "key_points": [str(item).strip() for item in key_points if str(item).strip()][:3],
        "tags": _normalize_tags([str(item).strip() for item in tags if str(item).strip()][:8]),
        "intelligence_source": "ai",
    }


def _parse_json_text(text: str) -> dict[str, Any]:
    cleaned = str(text or "").strip()
    if not cleaned:
        return {}
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(cleaned[start : end + 1])
        except json.JSONDecodeError:
            return {}
    return {}


def _normalize_tags(tags: list[str]) -> list[str]:
    alias_map = {
        "solo句子": "Solo",
        "solo乐句": "Solo",
        "旋律句子": "Solo",
        "节拍": "节奏",
        "主拍": "节奏",
        "右手": "拨弦",
        "起音": "拨弦",
        "音头": "拨弦",
        "和声": "和弦",
        "音阶指板": "指板",
        "情绪表达": "表达",
    }
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in tags:
        tag = str(raw or "").strip()
        if not tag:
            continue
        lowered = tag.lower()
        mapped = alias_map.get(lowered, tag)
        if mapped in seen:
            continue
        seen.add(mapped)
        normalized.append(mapped)
    return normalized[:8]
