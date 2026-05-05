from __future__ import annotations

from collections import Counter

from services.coach_sessions import list_sessions
from services.video_matching import match_related_videos


TOPIC_DEFINITIONS = {
    "rhythm": {
        "label": "主拍与节奏稳定",
        "reason_tag": "补主拍",
        "keywords": ["节奏", "主拍", "切分", "进入点", "拖拍", "抢拍", "落拍", "拍点", "掉拍"],
        "course_keywords": ["节奏", "切分", "弱起", "shuffle", "主拍"],
        "task": "保持当前速度，先把最容易掉拍的 2 到 4 小节做循环，只盯主拍和进入点。",
        "minutes": 12,
        "verify_step": "练完后回到当前歌曲，先只验证进入点和每句第一拍。",
    },
    "picking": {
        "label": "拨弦与起音清晰度",
        "reason_tag": "补拨弦",
        "keywords": ["拨弦", "起音", "音头", "清晰", "杂音", "触弦", "力度"],
        "course_keywords": ["拨弦", "右手", "经济拨弦", "混合交替拨弦"],
        "task": "先不要追求速度，先把每个关键音拨清楚，让重拍和起音更干净。",
        "minutes": 10,
        "verify_step": "练完后回到当前歌曲，确认关键音的起音和重拍是否更干净。",
    },
    "solo": {
        "label": "Solo 句子推进与表达",
        "reason_tag": "补句子推进",
        "keywords": ["solo", "句子", "推进", "尾奏", "乐句", "旋律"],
        "course_keywords": ["solo", "乐句", "音阶"],
        "task": "先拆开练句子连接处，保证每句起点稳定，再把整段串起来。",
        "minutes": 15,
        "verify_step": "练完后回到当前歌曲，听每句连接处是不是更顺，别急着提速。",
    },
    "theory": {
        "label": "乐理 / 指板理解",
        "reason_tag": "补乐理",
        "keywords": ["乐理", "和弦", "音阶", "指板", "音程"],
        "course_keywords": ["乐理", "和弦", "音阶", "指板", "音程"],
        "task": "先补基础理解，再回到歌曲里验证，不要只靠反复刷段落。",
        "minutes": 8,
        "verify_step": "练完后回到当前歌曲，看刚才不顺的地方是不是更容易理解和记住。",
    },
}


def _collect_song_practice_text(song_id: str) -> tuple[str, list[dict]]:
    sessions = [session for session in list_sessions() if session.get("song_id") == song_id]
    chunks: list[str] = []
    for session in sessions[:8]:
        analysis = session.get("analysis") or {}
        chunks.extend(issue.get("message", "") for issue in analysis.get("issues", []) if issue.get("message"))
        chunks.extend(advice for advice in analysis.get("advice", []) if advice)
        if analysis.get("coach_feedback"):
            chunks.append(analysis["coach_feedback"])
    return " ".join(chunks), sessions


def _detect_focus_topic(song: dict, related_videos: list[dict], practice_text: str) -> str:
    corpus = " ".join([
        song.get("title", ""),
        song.get("artist", ""),
        practice_text,
        " ".join(video.get("title", "") for video in related_videos[:6]),
        " ".join(video.get("description", "") for video in related_videos[:6]),
        " ".join(video.get("summary", "") for video in related_videos[:6]),
        " ".join(video.get("learning_focus", "") for video in related_videos[:6]),
        " ".join(video.get("recommended_for", "") for video in related_videos[:6]),
        " ".join(" ".join(video.get("key_points") or []) for video in related_videos[:6]),
        " ".join(" ".join(video.get("tags") or []) for video in related_videos[:6]),
    ]).lower()

    scores: Counter[str] = Counter()
    for topic, config in TOPIC_DEFINITIONS.items():
        for keyword in config["keywords"]:
            if keyword.lower() in corpus:
                scores[topic] += 1

    if scores:
        return scores.most_common(1)[0][0]

    if related_videos:
        return "solo"
    return "rhythm"


def _recommend_courses(courses: list[dict], topic_key: str, limit: int = 2) -> list[dict]:
    config = TOPIC_DEFINITIONS[topic_key]
    scored: list[tuple[int, dict]] = []
    for course in courses:
        haystack = " ".join([
            course.get("title", ""),
            course.get("description", ""),
            course.get("summary", ""),
            course.get("learning_focus", ""),
            course.get("recommended_for", ""),
            " ".join(course.get("key_points") or []),
            " ".join(course.get("tags") or []),
            course.get("series", ""),
            course.get("level", ""),
        ]).lower()
        score = sum(1 for keyword in config["course_keywords"] if keyword.lower() in haystack)
        if course.get("intelligence_source") == "ai":
            score += 6
        if topic_key in str(course.get("learning_focus", "")).lower():
            score += 4
        if score <= 0:
            continue
        scored.append((score, course))

    scored.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    return [
        {
            "id": course.get("id", ""),
            "title": course.get("title", ""),
            "series": course.get("series", ""),
            "level": course.get("level", ""),
            "reason": build_course_reason(course, config["label"]),
            "reason_tag": config["reason_tag"],
            "focus": course.get("learning_focus", ""),
            "summary": course.get("summary", ""),
        }
        for score, course in scored[:limit]
    ]


def _recommend_videos(related_videos: list[dict], topic_key: str, limit: int = 2) -> list[dict]:
    config = TOPIC_DEFINITIONS[topic_key]
    scored: list[tuple[int, dict]] = []
    for video in related_videos:
        haystack = " ".join([
            video.get("title", ""),
            video.get("description", ""),
            video.get("category", ""),
            video.get("summary", ""),
            video.get("learning_focus", ""),
            video.get("recommended_for", ""),
            " ".join(video.get("key_points") or []),
            " ".join(video.get("tags") or []),
        ]).lower()
        extra = sum(1 for keyword in config["keywords"] if keyword.lower() in haystack)
        score = int(video.get("match_score", 0)) + extra * 10
        if video.get("intelligence_source") == "ai":
            score += 6
        scored.append((score, video))

    scored.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    return [
        {
            "id": video.get("id", ""),
            "title": video.get("title", ""),
            "reason": build_video_reason(video, config["label"]),
            "reason_tag": config["reason_tag"],
            "focus": video.get("learning_focus", ""),
            "summary": video.get("summary", ""),
        }
        for score, video in scored[:limit]
    ]


def build_song_learning_recommendations(song: dict, index: dict) -> dict:
    related_videos = match_related_videos(song, index.get("videos", []), limit=6)
    practice_text, sessions = _collect_song_practice_text(song.get("id", ""))
    topic_key = _detect_focus_topic(song, related_videos, practice_text)
    topic = TOPIC_DEFINITIONS[topic_key]

    latest_session = sessions[0] if sessions else None
    tempo_mode = ""
    if latest_session:
        tempo_mode = (latest_session.get("analysis") or {}).get("tempo_mode", "") or latest_session.get("tempo_mode", "")

    focus_reason = (
        f"最近你在《{song.get('title', '')}》上的练习记录里，和“{topic['label']}”相关的问题出现得更频繁。"
        if latest_session
        else f"你当前打开的是《{song.get('title', '')}》，先围绕最容易形成帮助的“{topic['label']}”补一轮。"
    )
    if related_videos:
        top_focuses = [video.get("learning_focus", "") for video in related_videos[:3] if video.get("learning_focus")]
        if top_focuses:
            focus_reason += f" 你现有相关视频里，最集中出现的也是：{' / '.join(top_focuses[:2])}。"

    next_action = topic["task"]
    if tempo_mode:
        next_action = f"{tempo_mode} 下，{next_action}"

    recommended_courses = _recommend_courses(index.get("courses", []), topic_key, limit=2)
    recommended_videos = _recommend_videos(related_videos, topic_key, limit=2)

    learning_path = [
        {
            "step": 1,
            "type": "song",
            "title": f"先练《{song.get('title', '')}》当前版本",
            "action": next_action,
            "minutes": topic["minutes"],
        }
    ]

    if recommended_courses:
        first_course = recommended_courses[0]
        learning_path.append(
            {
                "step": 2,
                "type": "course",
                "title": f"补一节系统课：{first_course.get('title', '')}",
                "action": f"先看 {first_course.get('series', '')} / {first_course.get('level', '')}，重点围绕“{topic['label']}”。",
                "minutes": 8,
                "target_id": first_course.get("id", ""),
            }
        )

    if recommended_videos:
        first_video = recommended_videos[0]
        learning_path.append(
            {
                "step": len(learning_path) + 1,
                "type": "video",
                "title": f"看一条相关学习视频：{first_video.get('title', '')}",
                "action": "只盯这一条视频里最相关的演示或讲解，不要一次看太多。",
                "minutes": 6,
                "target_id": first_video.get("id", ""),
            }
        )

    learning_path.append(
        {
            "step": len(learning_path) + 1,
            "type": "verify",
            "title": f"回到《{song.get('title', '')}》验证",
            "action": topic["verify_step"],
            "minutes": 5,
        }
    )

    total_minutes = sum(int(step.get("minutes", 0) or 0) for step in learning_path)
    today_plan = {
        "title": f"今天先围绕《{song.get('title', '')}》练一轮",
        "total_minutes": total_minutes,
        "summary": f"先补“{topic['label']}”，再用最相关的系统课和学习视频各补一轮，最后回到歌曲验证。",
        "checklist": [
            f"先练当前歌曲 {topic['minutes']} 分钟，别急着提速。",
            "系统课只看最相关的一节，不要分散。",
            "学习视频只抓一个重点演示或讲解。",
            "最后回到歌曲里验证一个最关键的问题点。",
        ],
    }

    return {
        "focus_topic": topic["label"],
        "focus_tag": topic["reason_tag"],
        "reason": focus_reason,
        "coach_brief": build_learning_coach_brief(song, topic["label"], latest_session),
        "today_plan": today_plan,
        "next_task": {
            "title": f"继续练《{song.get('title', '')}》当前版本",
            "action": next_action,
            "minutes": topic["minutes"],
            "verify_step": topic["verify_step"],
        },
        "recommended_courses": recommended_courses,
        "recommended_videos": recommended_videos,
        "learning_path": learning_path,
        "recommended_song": {
            "id": song.get("id", ""),
            "title": song.get("title", ""),
        },
    }


def build_course_reason(course: dict, topic_label: str) -> str:
    focus = str(course.get("learning_focus", "")).strip()
    if focus and focus != topic_label:
        return f"这节课主讲“{focus}”，能从侧面补当前更核心的“{topic_label}”。"
    if course.get("recommended_for"):
        return str(course.get("recommended_for"))
    return f"对应当前重点：{topic_label}"


def build_video_reason(video: dict, topic_label: str) -> str:
    focus = str(video.get("learning_focus", "")).strip()
    if focus and focus != topic_label:
        return f"这条视频更偏“{focus}”，但正好能补你当前这首歌卡住的地方。"
    if video.get("recommended_for"):
        return str(video.get("recommended_for"))
    return f"与当前歌曲直接相关，适合补“{topic_label}”。"


def build_learning_coach_brief(song: dict, topic_label: str, latest_session: dict | None) -> str:
    if latest_session:
        return f"先别急着扩新内容，先把《{song.get('title', '')}》里和“{topic_label}”直接相关的问题补稳。"
    return f"你现在最值得先补的是“{topic_label}”，先围绕当前这首歌完成一轮闭环。"
