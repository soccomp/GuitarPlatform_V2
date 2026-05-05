from __future__ import annotations

from services.video_matching import normalize_text


def build_video_intelligence_summary(index: dict) -> dict:
    videos = index.get("videos", [])
    ready = [video for video in videos if video.get("transcript_available") or video.get("transcript_preview")]
    pending = [video for video in videos if video not in ready]
    prioritized = sorted(
        (build_video_backlog_item(video, index.get("songs", [])) for video in pending),
        key=lambda item: (-item["score"], item["title"]),
    )[:6]
    return {
        "total": len(videos),
        "ready": len(ready),
        "pending": len(pending),
        "prioritized_items": prioritized,
        "prioritized_ids": [item["id"] for item in prioritized],
    }


def build_course_intelligence_summary(index: dict) -> dict:
    courses = index.get("courses", [])
    ready = [course for course in courses if course.get("transcript_available") or course.get("transcript_preview")]
    pending = [course for course in courses if course not in ready]
    prioritized = sorted(
        (build_course_backlog_item(course) for course in pending),
        key=lambda item: (-item["score"], item["title"]),
    )[:6]
    return {
        "total": len(courses),
        "ready": len(ready),
        "pending": len(pending),
        "prioritized_items": prioritized,
        "prioritized_ids": [item["id"] for item in prioritized],
    }


def build_video_backlog_item(video: dict, songs: list[dict]) -> dict:
    title = str(video.get("title", "")).strip()
    category = str(video.get("category", "")).strip()
    tags = video.get("tags") or []
    reasons = []
    score = 100
    title_key = normalize_text(title)

    song_hits = []
    for song in songs:
        song_title = str(song.get("title", "")).strip()
        if not song_title:
            continue
        song_key = normalize_text(song_title)
        if song_key and song_key in title_key:
            song_hits.append(song_title)

    if song_hits:
        score += 35
        reasons.append(f"与歌曲“{song_hits[0]}”直接相关")

    lowered = title.lower()
    if any(keyword in lowered for keyword in ["solo", "cover", "lesson"]):
        score += 15
        reasons.append("更适合直接拿来对照练歌")
    if any(keyword in title for keyword in ["教学", "弹唱", "尾奏", "前奏", "间奏"]):
        score += 20
        reasons.append("标题显示是高价值教学/对照内容")
    if category and category != "未分类":
        score += 8
    if tags:
        score += min(len(tags), 3) * 3

    return {
        "id": video.get("id", ""),
        "title": title,
        "subtitle": video.get("author") or category or "学习视频",
        "reason": "；".join(reasons) or "这条视频还没有文字内容，补完后更适合做推荐、搜索和重点提炼。",
        "score": score,
    }


def build_course_backlog_item(course: dict) -> dict:
    title = str(course.get("title", "")).strip()
    series = str(course.get("series", "")).strip()
    level = str(course.get("level", "")).strip()
    tags = course.get("tags") or []
    score = 100
    reasons = []
    haystack = f"{title} {level} {' '.join(tags)}".lower()

    if any(keyword in haystack for keyword in ["节奏", "主拍", "切分", "shuffle"]):
        score += 25
        reasons.append("补齐后更适合给练歌节奏问题做推荐")
    if any(keyword in haystack for keyword in ["solo", "乐句", "音阶", "拨弦", "右手"]):
        score += 18
        reasons.append("课程内容和歌曲练习结合度较高")
    if any(keyword in haystack for keyword in ["乐理", "音程", "和弦", "指板"]):
        score += 12
        reasons.append("补齐后更适合做知识点问答和摘要")
    if series:
        score += 5

    return {
        "id": course.get("id", ""),
        "title": title,
        "subtitle": f"{series} / {level}".strip(" /"),
        "reason": "；".join(reasons) or "这节课还没有文字内容，补完后更适合做问答、重点提炼和学习推荐。",
        "score": score,
    }
