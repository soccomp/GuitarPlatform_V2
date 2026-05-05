from __future__ import annotations

import re


COURSE_TOPIC_RULES = [
    {
        "topic": "乐理与指板",
        "keywords": ["乐理", "音阶", "音程", "和弦", "指板", "调式", "琶音", "首调", "固定调", "平均律"],
        "summary": "这节课更偏基础理解，适合在歌曲练习遇到“会弹但不理解”的地方回补概念。",
        "focus": "先补乐理和指板理解，再回到歌曲里验证记忆和应用。",
        "recommended_for": "适合在歌曲里的和弦、音阶、指板位置总记不稳时回看。",
    },
    {
        "topic": "节奏与主拍",
        "keywords": ["节奏", "主拍", "切分", "shuffle", "弱起", "律动", "拍点"],
        "summary": "这节课重点更偏节奏、主拍和律动，适合在练歌时补拍点稳定性。",
        "focus": "先把主拍、切分和进入点练稳，再回到歌曲里串联。",
        "recommended_for": "适合在你总是抢拍、拖拍或句子推进不稳时回看。",
    },
    {
        "topic": "拨弦与右手",
        "keywords": ["拨弦", "右手", "picking", "触弦", "起音", "清晰度", "扫拨", "交替拨弦"],
        "summary": "这节课更偏右手动作和起音清晰度，适合补关键音不干净的问题。",
        "focus": "先让关键音拨清楚，再回到歌曲里验证重拍和起音。",
        "recommended_for": "适合在你觉得音头不清晰、右手不稳定时回看。",
    },
    {
        "topic": "Solo 句子",
        "keywords": ["solo", "乐句", "句子", "旋律", "前奏", "尾奏", "间奏", "推弦", "揉弦"],
        "summary": "这节课更偏 solo 句子、连接和表达，适合拆段对照学习。",
        "focus": "先拆句子连接和进入点，再回到整段串联和表达。",
        "recommended_for": "适合在前奏、间奏或尾奏总是接不顺的时候回看。",
    },
    {
        "topic": "和弦与伴奏",
        "keywords": ["和弦", "伴奏", "扫弦", "分解", "节奏型", "弹唱"],
        "summary": "这节课更偏和弦与伴奏框架，适合补歌曲底层支撑和伴奏型。",
        "focus": "先把和弦框架和伴奏型练稳，再回到整首歌。",
        "recommended_for": "适合在你能弹旋律但歌曲框架撑不稳的时候回看。",
    },
]


def build_course_intelligence(course: dict, transcript_text: str = "") -> dict:
    merged = dict(course)
    title = str(course.get("title", "")).strip()
    series = str(course.get("series", "")).strip()
    level = str(course.get("level", "")).strip()
    description = str(course.get("description", "")).strip()
    tags = _clean_tags(course.get("tags") or [])
    transcript_preview = _build_transcript_preview(transcript_text)

    corpus = " ".join([title, series, level, description, " ".join(tags), transcript_preview]).lower()
    matched = [rule for rule in COURSE_TOPIC_RULES if any(keyword.lower() in corpus for keyword in rule["keywords"])]
    primary = matched[0] if matched else COURSE_TOPIC_RULES[0]

    merged["learning_focus"] = primary["topic"]
    merged["summary"] = _build_summary(primary, title, transcript_preview)
    merged["recommended_for"] = primary["recommended_for"]
    merged["key_points"] = _build_key_points(primary, title, transcript_preview, description)
    merged["transcript_preview"] = transcript_preview
    merged["transcript_available"] = bool(transcript_preview)
    merged["tags"] = _derive_tags(tags, matched, title, level)
    return merged


def _clean_tags(values: list[str]) -> list[str]:
    result = []
    seen = set()
    for raw in values:
        tag = str(raw or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        result.append(tag)
    return result


def _build_transcript_preview(text: str, limit: int = 180) -> str:
    compact = re.sub(r"\s+", " ", str(text or "")).strip()
    if not compact:
        return ""
    return compact[:limit].rstrip("，。；,. ") + ("..." if len(compact) > limit else "")


def _derive_tags(existing_tags: list[str], matched: list[dict], title: str, level: str) -> list[str]:
    tags = list(existing_tags)
    for rule in matched[:3]:
        if rule["topic"] not in tags:
            tags.append(rule["topic"])

    haystack = f"{title} {level}".lower()
    keyword_tags = [
        ("乐理", "乐理"),
        ("节奏", "节奏"),
        ("solo", "Solo"),
        ("和弦", "和弦"),
        ("音阶", "音阶"),
        ("拨弦", "拨弦"),
        ("右手", "右手"),
    ]
    for keyword, tag in keyword_tags:
        if keyword in haystack and tag not in tags:
            tags.append(tag)
    return tags[:8]


def _build_summary(primary: dict, title: str, transcript_preview: str) -> str:
    if transcript_preview:
        return f"{primary['summary']} 当前已经有文字内容，适合继续做问答、摘要和相关推荐。"
    return f"{primary['summary']} 当前主要依据课程标题“{title}”做理解。"


def _build_key_points(primary: dict, title: str, transcript_preview: str, description: str) -> list[str]:
    points = [primary["focus"]]
    if transcript_preview:
        points.append("这节课已经有文字内容，后面更适合做课程问答和重点提炼。")
    elif description:
        points.append("当前主要依据课程标题和分章信息做理解，后面补 transcript 会更准。")
    else:
        points.append("当前主要依据课程标题做理解，后面补 transcript 会更准。")

    if any(keyword in title.lower() for keyword in ["solo", "前奏", "尾奏", "间奏"]):
        points.append("适合拆段回看，重点对照句子连接和表达。")
    elif any(keyword in title for keyword in ["乐理", "音阶", "和弦"]):
        points.append("适合先补概念，再回到歌曲里验证应用。")
    else:
        points.append("建议先抓一个重点，不要一节课里同时想解决太多问题。")
    return points[:3]
