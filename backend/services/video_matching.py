from __future__ import annotations

import re


SPLIT_PATTERN = re.compile(r"[\s_\-./|()（）【】\[\]·,，:：]+")


def normalize_text(text: str) -> str:
    return "".join(part for part in SPLIT_PATTERN.split((text or "").lower()) if part)


GENERIC_VIDEO_WORDS = {
    "solo",
    "教学",
    "弹唱",
    "伴奏",
    "吉他",
    "电吉他",
    "cover",
    "lesson",
    "guitar",
    "youtube",
    "xhs",
}


def extract_keywords(title: str, artist: str = "") -> list[str]:
    tokens: list[str] = []
    for value in (title, artist):
        for part in SPLIT_PATTERN.split((value or "").strip()):
            token = part.strip().lower()
            if len(token) >= 2 and token not in GENERIC_VIDEO_WORDS:
                tokens.append(token)
    seen: set[str] = set()
    result: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.add(token)
            result.append(token)
    return result


def match_related_videos(song: dict, videos: list[dict], limit: int = 8) -> list[dict]:
    title = (song.get("title") or "").strip()
    artist = (song.get("artist") or "").strip()
    if not title:
        return []

    title_key = normalize_text(title)
    artist_key = normalize_text(artist)
    title_keywords = extract_keywords(title)
    artist_keywords = extract_keywords("", artist)

    scored: list[tuple[int, dict]] = []
    for video in videos:
        haystack = " ".join(
            str(video.get(field, "") or "")
            for field in ("title", "description", "path", "author", "category")
        )
        extra = " ".join(video.get("tags") or [])
        normalized = normalize_text(f"{haystack} {extra}")
        if not normalized:
            continue

        score = 0
        reasons: list[str] = []

        if title_key and title_key in normalized:
            score += 100
            reasons.append("歌名命中")

        if artist_key and artist_key in normalized:
            score += 15
            reasons.append("歌手命中")

        title_keyword_hits = sum(1 for keyword in title_keywords if normalize_text(keyword) in normalized)
        artist_keyword_hits = sum(1 for keyword in artist_keywords if normalize_text(keyword) in normalized)

        if title_keyword_hits:
            score += title_keyword_hits * 12
            reasons.append(f"{title_keyword_hits} 个歌名关键词命中")

        if artist_keyword_hits:
            score += artist_keyword_hits * 4
            reasons.append(f"{artist_keyword_hits} 个歌手关键词命中")

        has_strong_song_match = bool(title_key and title_key in normalized) or title_keyword_hits >= 1
        if not has_strong_song_match:
            continue

        enriched = dict(video)
        enriched["match_score"] = score
        enriched["match_reasons"] = reasons
        scored.append((score, enriched))

    scored.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    return [item for _, item in scored[:limit]]
