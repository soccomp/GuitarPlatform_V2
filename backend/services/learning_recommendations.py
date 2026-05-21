from __future__ import annotations

from collections import Counter

from services.coach_sessions import list_sessions
from services.learning_signals import SIGNAL_RULES, build_signal_scores, signal_labels_from_scores
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

    signal_scores = build_signal_scores(corpus)
    if signal_scores.get("rhythm"):
        scores["rhythm"] += signal_scores["rhythm"] * 2
    if signal_scores.get("picking"):
        scores["picking"] += signal_scores["picking"] * 2
    if signal_scores.get("solo"):
        scores["solo"] += signal_scores["solo"] * 2
    if signal_scores.get("theory") or signal_scores.get("fretboard"):
        scores["theory"] += (signal_scores.get("theory", 0) + signal_scores.get("fretboard", 0)) * 2
    if signal_scores.get("chords"):
        scores["theory"] += signal_scores["chords"]

    if scores:
        return scores.most_common(1)[0][0]

    if related_videos:
        return "solo"
    return "rhythm"


def _recommend_courses(courses: list[dict], topic_key: str, limit: int = 2) -> list[dict]:
    config = TOPIC_DEFINITIONS[topic_key]
    scored: list[tuple[int, dict]] = []
    topic_signal_labels = _topic_signal_labels(topic_key)
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
        score += _signal_overlap_score(course, topic_signal_labels)
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
            "reason": build_course_reason(course, config["label"], topic_signal_labels),
            "reason_tag": config["reason_tag"],
            "focus": course.get("learning_focus", ""),
            "summary": course.get("summary", ""),
        }
        for score, course in scored[:limit]
    ]


def _recommend_videos(related_videos: list[dict], topic_key: str, limit: int = 2) -> list[dict]:
    config = TOPIC_DEFINITIONS[topic_key]
    scored: list[tuple[int, dict]] = []
    topic_signal_labels = _topic_signal_labels(topic_key)
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
        score = int(video.get("match_score", 0)) + extra * 10 + _signal_overlap_score(video, topic_signal_labels)
        if video.get("intelligence_source") == "ai":
            score += 6
        scored.append((score, video))

    scored.sort(key=lambda item: (-item[0], item[1].get("title", "")))
    return [
        {
            "id": video.get("id", ""),
            "title": video.get("title", ""),
            "reason": build_video_reason(video, config["label"], topic_signal_labels),
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
    signal_labels = _topic_signal_labels(topic_key)

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
    if signal_labels:
        focus_reason += f" 这轮学习更值得优先补：{' / '.join(signal_labels[:2])}。"

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
        "coach_diagnosis": build_learning_coach_diagnosis(song, topic["label"], signal_labels, related_videos, recommended_courses, recommended_videos),
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


def build_course_reason(course: dict, topic_label: str, signal_labels: list[str]) -> str:
    focus = str(course.get("learning_focus", "")).strip()
    matching_labels = _matching_signal_labels(course, signal_labels)
    if matching_labels:
        return f"这节课和你当前要补的 { ' / '.join(matching_labels[:2]) } 直接对上，适合先看再回歌里验证。"
    if focus and focus != topic_label:
        return f"这节课主讲“{focus}”，能从侧面补当前更核心的“{topic_label}”。"
    if course.get("recommended_for"):
        return str(course.get("recommended_for"))
    return f"对应当前重点：{topic_label}"


def build_video_reason(video: dict, topic_label: str, signal_labels: list[str]) -> str:
    focus = str(video.get("learning_focus", "")).strip()
    matching_labels = _matching_signal_labels(video, signal_labels)
    if matching_labels:
        return f"这条视频最适合先补 { ' / '.join(matching_labels[:2]) }，看完马上回当前歌曲验证会更有帮助。"
    if focus and focus != topic_label:
        return f"这条视频更偏“{focus}”，但正好能补你当前这首歌卡住的地方。"
    if video.get("recommended_for"):
        return str(video.get("recommended_for"))
    return f"与当前歌曲直接相关，适合补“{topic_label}”。"


def build_learning_coach_brief(song: dict, topic_label: str, latest_session: dict | None) -> str:
    if latest_session:
        return f"先别急着扩新内容，先把《{song.get('title', '')}》里和“{topic_label}”直接相关的问题补稳。"
    return f"你现在最值得先补的是“{topic_label}”，先围绕当前这首歌完成一轮闭环。"


def build_learning_coach_diagnosis(
    song: dict,
    topic_label: str,
    signal_labels: list[str],
    related_videos: list[dict],
    recommended_courses: list[dict],
    recommended_videos: list[dict],
) -> str:
    content_hits = []
    if recommended_courses:
        content_hits.append("系统课")
    if recommended_videos:
        content_hits.append("学习视频")
    if related_videos and "学习视频" not in content_hits:
        content_hits.append("相关视频")

    signal_text = " / ".join(signal_labels[:2]) if signal_labels else topic_label
    if content_hits:
        return f"当前判断你更需要先补 {signal_text}，而且平台里已经有对应的{' + '.join(content_hits)}可以马上接上。"
    return f"当前判断你更需要先补 {signal_text}，建议先围绕当前歌曲完成一轮针对性练习。"


def _topic_signal_labels(topic_key: str) -> list[str]:
    mapping = {
        "rhythm": ["节奏"],
        "picking": ["拨弦", "表达"],
        "solo": ["Solo", "表达"],
        "theory": ["乐理", "指板", "和弦"],
    }
    return mapping.get(topic_key, [])


def _item_signal_labels(item: dict) -> list[str]:
    signal_scores = build_signal_scores(
        item.get("title", ""),
        item.get("description", ""),
        item.get("summary", ""),
        item.get("learning_focus", ""),
        item.get("recommended_for", ""),
        " ".join(item.get("key_points") or []),
        " ".join(item.get("tags") or []),
        item.get("series", ""),
        item.get("level", ""),
        item.get("category", ""),
        item.get("author", ""),
    )
    labels = signal_labels_from_scores(signal_scores, limit=4)
    for tag in item.get("tags") or []:
        normalized = str(tag or "").strip()
        if normalized in {config["label"] for config in SIGNAL_RULES.values()} and normalized not in labels:
            labels.append(normalized)
    return labels[:4]


def _signal_overlap_score(item: dict, target_labels: list[str]) -> int:
    if not target_labels:
        return 0
    labels = _item_signal_labels(item)
    matches = [label for label in labels if label in target_labels]
    return len(matches) * 9


def _matching_signal_labels(item: dict, target_labels: list[str]) -> list[str]:
    if not target_labels:
        return []
    return [label for label in _item_signal_labels(item) if label in target_labels]
