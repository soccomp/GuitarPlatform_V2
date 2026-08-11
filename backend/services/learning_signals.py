from __future__ import annotations

from collections import Counter
import re


SIGNAL_RULES = {
    "rhythm": {
        "label": "节奏",
        "keywords": ["节奏", "主拍", "切分", "弱起", "律动", "shuffle", "拍点", "拖拍", "抢拍", "掉拍"],
    },
    "picking": {
        "label": "拨弦",
        "keywords": ["拨弦", "右手", "交替拨弦", "经济拨弦", "picking", "pick", "起音", "音头", "触弦", "清晰度"],
    },
    "solo": {
        "label": "Solo",
        "keywords": ["solo", "前奏", "间奏", "尾奏", "乐句", "句子", "旋律", "推弦", "揉弦"],
    },
    "theory": {
        "label": "乐理",
        "keywords": ["乐理", "音阶", "调式", "音程", "和声", "首调", "固定调", "平均律"],
    },
    "fretboard": {
        "label": "指板",
        "keywords": ["指板", "把位", "琶音", "位置", "音名", "品位"],
    },
    "chords": {
        "label": "和弦",
        "keywords": ["和弦", "伴奏", "扫弦", "分解", "节奏型", "弹唱", "和声框架"],
    },
    "expression": {
        "label": "表达",
        "keywords": ["表达", "动态", "力度", "情绪", "音色", "句尾", "收尾", "推进感"],
    },
}


WORD_SPLIT = re.compile(r"[\s,_./|()（）【】\[\]·:：;；!?！？]+")


def build_signal_scores(*texts: str) -> dict[str, int]:
    corpus = " ".join(str(text or "") for text in texts).lower()
    scores: Counter[str] = Counter()
    for key, config in SIGNAL_RULES.items():
        for keyword in config["keywords"]:
            if keyword.lower() in corpus:
                scores[key] += 1
    return dict(scores)


def signal_labels_from_scores(scores: dict[str, int], limit: int = 4) -> list[str]:
    ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    labels: list[str] = []
    for key, score in ranked:
        if score <= 0:
            continue
        labels.append(SIGNAL_RULES[key]["label"])
        if len(labels) >= limit:
            break
    return labels


def merge_signal_tags(existing_tags: list[str], *texts: str, limit: int = 8) -> list[str]:
    tags: list[str] = []
    seen: set[str] = set()

    for raw in existing_tags:
        tag = str(raw or "").strip()
        if not tag or tag in seen:
            continue
        seen.add(tag)
        tags.append(tag)

    for label in signal_labels_from_scores(build_signal_scores(*texts), limit=limit):
        if label in seen:
            continue
        seen.add(label)
        tags.append(label)
        if len(tags) >= limit:
            break

    return tags[:limit]


def build_signal_summary(*texts: str) -> str:
    labels = signal_labels_from_scores(build_signal_scores(*texts), limit=3)
    return " / ".join(labels)


def normalize_tokens(*texts: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for part in WORD_SPLIT.split(str(text or "").strip()):
            token = part.strip().lower()
            if len(token) < 2 or token in seen:
                continue
            seen.add(token)
            tokens.append(token)
    return tokens
