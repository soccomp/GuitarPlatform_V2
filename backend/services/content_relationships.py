from __future__ import annotations

from services.learning_recommendations import build_song_learning_recommendations
from services.video_matching import match_related_videos


def build_related_songs_for_video(video: dict, index: dict, limit: int = 4) -> list[dict]:
    songs = index.get("songs", [])
    videos = index.get("videos", [])
    target_id = video.get("id", "")
    matches: list[dict] = []

    for song in songs:
        score = 0
        reason = ""

        related_videos = match_related_videos(song, videos, limit=8)
        direct_match = next((item for item in related_videos if item.get("id") == target_id), None)
        if direct_match:
            score += int(direct_match.get("match_score", 0)) + 25
            reasons = direct_match.get("match_reasons") or []
            reason = "，".join(reasons[:2]) if reasons else "和这首歌直接相关"

        recommendations = build_song_learning_recommendations(song, index)
        recommended_video = next(
            (item for item in recommendations.get("recommended_videos", []) if item.get("id") == target_id),
            None,
        )
        if recommended_video:
            score += 45
            focus = recommendations.get("focus_topic", "")
            reason = f"适合回到这首歌补“{focus}”" if focus else (recommended_video.get("reason") or reason)

        if score <= 0:
            continue

        matches.append(
            {
                "id": song.get("id", ""),
                "title": song.get("title", ""),
                "artist": song.get("artist", ""),
                "reason": reason or "这条视频适合回到这首歌做对照练习",
                "score": score,
            }
        )

    matches.sort(key=lambda item: (-item["score"], item["title"]))
    return matches[:limit]


def build_related_songs_for_course(course: dict, index: dict, limit: int = 4) -> list[dict]:
    songs = index.get("songs", [])
    target_id = course.get("id", "")
    matches: list[dict] = []

    for song in songs:
        recommendations = build_song_learning_recommendations(song, index)
        recommended_course = next(
            (item for item in recommendations.get("recommended_courses", []) if item.get("id") == target_id),
            None,
        )
        if not recommended_course:
            continue

        focus = recommendations.get("focus_topic", "")
        matches.append(
            {
                "id": song.get("id", ""),
                "title": song.get("title", ""),
                "artist": song.get("artist", ""),
                "reason": f"这首歌当前更适合补“{focus}”" if focus else (recommended_course.get("reason") or ""),
                "score": 90 if focus else 70,
            }
        )

    matches.sort(key=lambda item: (-item["score"], item["title"]))
    return matches[:limit]
