from __future__ import annotations

import re
from pathlib import Path

from services.learning_signals import build_signal_summary, merge_signal_tags


VIDEO_TOPIC_RULES = [
    {
        "topic": "歌曲练习",
        "keywords": ["歌曲", "cover", "弹唱", "演示", "练习", "版本"],
        "summary": "适合直接对照歌曲练习，帮助你把内容尽快带回到实际演奏里。",
        "focus": "先拿来对照当前歌曲版本，抓节奏、句子和演奏处理。",
    },
    {
        "topic": "Solo 句子",
        "keywords": ["solo", "尾奏", "前奏", "间奏", "乐句", "旋律"],
        "summary": "更偏向 solo 句子、连接和表达，适合拆段对照学习。",
        "focus": "先拆句子连接和进入点，再回到整段串联。",
    },
    {
        "topic": "节奏与主拍",
        "keywords": ["节奏", "主拍", "切分", "shuffle", "扫弦", "律动", "拍点"],
        "summary": "重点在节奏、主拍和律动控制，适合补当前歌曲的拍点稳定性。",
        "focus": "先盯主拍和切分边界，再考虑提速和装饰音。",
    },
    {
        "topic": "拨弦与右手",
        "keywords": ["拨弦", "右手", "pick", "picking", "触弦", "音头", "清晰度"],
        "summary": "更适合补拨弦、起音和右手动作，让关键音更干净。",
        "focus": "先让关键音更清楚，再回到整段练习验证起音。",
    },
    {
        "topic": "和弦与伴奏",
        "keywords": ["和弦", "伴奏", "节奏型", "扫弦型", "分解", "弹唱"],
        "summary": "偏向和弦与伴奏打法，适合补歌曲框架和伴奏手感。",
        "focus": "先把和弦框架和伴奏型练稳，再回到完整歌曲。",
    },
    {
        "topic": "乐理与指板",
        "keywords": ["乐理", "音阶", "和声", "音程", "指板", "调式", "琶音"],
        "summary": "更偏知识理解，适合在歌曲卡住时补概念和指板理解。",
        "focus": "先补概念理解，再回到歌曲里验证记忆和手感。",
    },
]


COMPANION_TEXT_SUFFIXES = (".md", ".txt", ".srt", ".vtt")


def find_video_transcript(relative_video_path: Path, root_dir: Path) -> str:
    video_path = root_dir / relative_video_path
    stem = video_path.stem

    candidates = []
    for suffix in COMPANION_TEXT_SUFFIXES:
        candidates.append(video_path.with_suffix(suffix))
        candidates.append(video_path.parent / f"{stem}.transcript{suffix}")
        candidates.append(video_path.parent / f"{stem}.notes{suffix}")

    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.relative_to(root_dir).as_posix()

    return ""


def build_video_intelligence(video: dict, transcript_text: str = "") -> dict:
    title = str(video.get("title", "")).strip()
    description = str(video.get("description", "")).strip()
    author = str(video.get("author", "")).strip()
    category = str(video.get("category", "")).strip()
    tags = _clean_tags(video.get("tags") or [])
    transcript_preview = _build_transcript_preview(transcript_text)

    corpus = " ".join(
        part for part in [title, description, author, category, " ".join(tags), transcript_preview] if part
    ).lower()

    matched_topics = []
    for rule in VIDEO_TOPIC_RULES:
        if any(keyword.lower() in corpus for keyword in rule["keywords"]):
            matched_topics.append(rule)

    primary = matched_topics[0] if matched_topics else VIDEO_TOPIC_RULES[0]
    derived_tags = _derive_tags(matched_topics, title, description, tags, transcript_preview)
    key_points = _build_key_points(primary, title, transcript_preview, description)
    signal_summary = build_signal_summary(title, description, author, category, " ".join(tags), transcript_preview)

    summary = _build_summary(primary, title, description, transcript_preview, signal_summary)
    recommended_for = _build_recommended_for(primary, title, signal_summary)

    return {
        "summary": summary,
        "learning_focus": primary["topic"],
        "recommended_for": recommended_for,
        "key_points": key_points,
        "transcript_preview": transcript_preview,
        "transcript_available": bool(transcript_preview),
        "tags": derived_tags,
    }


def merge_video_intelligence(video: dict, transcript_text: str = "") -> dict:
    merged = dict(video)
    intelligence = build_video_intelligence(merged, transcript_text=transcript_text)
    merged.update(intelligence)
    if video.get("intelligence_source") == "ai":
        merged["summary"] = str(video.get("summary", "")).strip() or merged.get("summary", "")
        merged["learning_focus"] = str(video.get("learning_focus", "")).strip() or merged.get("learning_focus", "")
        merged["recommended_for"] = str(video.get("recommended_for", "")).strip() or merged.get("recommended_for", "")
        if video.get("key_points"):
            merged["key_points"] = list(video.get("key_points") or [])[:3]
        merged["tags"] = _merge_tags(list(video.get("tags") or []), list(merged.get("tags") or []))
        merged["intelligence_source"] = "ai"
    return merged


def read_video_transcript_text(transcript_path: str, root_dir: Path) -> str:
    if not transcript_path:
        return ""
    try:
        text = (root_dir / transcript_path).read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = (root_dir / transcript_path).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""
    return text


def _clean_tags(values: list[str]) -> list[str]:
    cleaned = []
    seen = set()
    for raw in values:
        tag = str(raw or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        cleaned.append(tag)
    return cleaned


def _merge_tags(primary: list[str], secondary: list[str]) -> list[str]:
    result = []
    seen = set()
    for raw in [*primary, *secondary]:
        tag = str(raw or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result[:8]


def _build_transcript_preview(text: str, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if not compact:
        return ""
    return compact[:limit].rstrip("，。；,. ") + ("..." if len(compact) > limit else "")


def _derive_tags(
    matched_topics: list[dict],
    title: str,
    description: str,
    existing_tags: list[str],
    transcript_preview: str,
) -> list[str]:
    tags = list(existing_tags)
    for rule in matched_topics[:3]:
        if rule["topic"] not in tags:
            tags.append(rule["topic"])

    text = f"{title} {description}".lower()
    keyword_tags = [
        ("beyond", "Beyond"),
        ("solo", "Solo"),
        ("cover", "Cover"),
        ("教学", "教学"),
        ("弹唱", "弹唱"),
        ("节奏", "节奏"),
        ("乐理", "乐理"),
        ("和弦", "和弦"),
    ]
    for keyword, tag in keyword_tags:
        if keyword in text and tag not in tags:
            tags.append(tag)
    return merge_signal_tags(tags[:8], title, description, transcript_preview)


def _build_key_points(primary: dict, title: str, transcript_preview: str, description: str) -> list[str]:
    points = [primary["focus"]]
    if transcript_preview:
        points.append("这条视频已经有文字内容，后面更适合做摘要、问答和相关推荐。")
    elif description:
        points.append("当前主要依据标题和备注做理解，后面补 transcript 后推荐会更准。")
    else:
        points.append("当前主要依据标题做理解，后面补简介或 transcript 后推荐会更准。")

    if any(keyword in title.lower() for keyword in ["solo", "尾奏", "前奏", "间奏"]):
        points.append("适合拿来对照句子处理、进入点和段落连接。")
    elif any(keyword in title for keyword in ["教学", "弹唱", "和弦"]):
        points.append("更适合先看讲解，再回到歌曲里验证动作和节奏。")
    else:
        points.append("建议先抓一个最相关的重点，不要一次想把整条视频都学完。")
    return points[:3]


def _build_summary(primary: dict, title: str, description: str, transcript_preview: str, signal_summary: str) -> str:
    if description:
        suffix = f" 重点维度集中在：{signal_summary}。" if signal_summary else ""
        return f"{primary['summary']} 当前备注显示它主要围绕“{title}”展开。{suffix}"
    if transcript_preview:
        suffix = f" 目前更像在补：{signal_summary}。" if signal_summary else ""
        return f"{primary['summary']} 这条视频已经带文字内容，适合后续继续提炼重点。{suffix}"
    suffix = f" 当前能识别到的重点维度包括：{signal_summary}。" if signal_summary else ""
    return f"{primary['summary']} 当前主要依据标题“{title}”做理解。{suffix}"


def _build_recommended_for(primary: dict, title: str, signal_summary: str) -> str:
    if primary["topic"] == "Solo 句子":
        return "适合在歌曲练习里卡住前奏、间奏或尾奏时拿来对照。"
    if primary["topic"] == "节奏与主拍":
        return "适合在你觉得节奏、主拍或切分不稳时补一轮。"
    if primary["topic"] == "拨弦与右手":
        return "适合在起音不干净、右手发力不稳时补一轮。"
    if primary["topic"] == "乐理与指板":
        return "适合在歌曲能弹出来但不知道为什么这样弹时补理解。"
    if primary["topic"] == "和弦与伴奏":
        return "适合先把和弦框架和伴奏型练稳，再回到整首歌。"
    if signal_summary:
        return f"适合先补“{signal_summary}”，再回到当前歌曲练习验证。"
    return f"适合围绕“{title}”做参考学习，再回到当前歌曲练习。"
