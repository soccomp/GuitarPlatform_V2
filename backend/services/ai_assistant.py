import os

import httpx


MINIMAX_API_KEY = os.environ.get("MINIMAX_API_KEY", "").strip()
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-M2.7"


class AssistantConfigurationError(RuntimeError):
    pass


def ensure_ai_configured() -> None:
    if not MINIMAX_API_KEY:
        raise AssistantConfigurationError("MINIMAX_API_KEY is not configured")


async def ask_course_question(course_title: str, transcript: str, question: str) -> str:
    ensure_ai_configured()

    system_prompt = (
        "你叫小霞，是哥的专属吉他学习助教。\n"
        f"用户正在学习课程：《{course_title}》。\n"
        "以下是当前课程的笔记/录音转写内容：\n"
        f"{transcript[:4000] if transcript else '(暂无笔记内容)'}\n\n"
        "请优先基于当前课程内容用中文回答用户问题。\n"
        "如果课程内容没有直接答案，可以补充通用吉他知识，但必须明确说明那部分是补充。"
    )

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        "temperature": 0.7,
        "max_tokens": 700,
    }
    return await _send_chat(payload)


async def generate_practice_plan(topic: str, level: str) -> str:
    ensure_ai_configured()

    payload = {
        "model": MINIMAX_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你叫小霞，是哥的专属吉他陪练助教。\n"
                    "请根据课程主题和难度等级生成 5 到 8 个循序渐进的练习任务，"
                    "并在最后附 2 到 3 条实用练习建议。"
                ),
            },
            {
                "role": "user",
                "content": f"课程主题：{topic}\n难度等级：{level}",
            },
        ],
        "temperature": 0.8,
        "max_tokens": 900,
    }
    return await _send_chat(payload)


async def _send_chat(payload: dict) -> str:
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            MINIMAX_BASE_URL,
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    response.raise_for_status()
    result = response.json()
    choices = result.get("choices") or []
    if not choices:
        raise RuntimeError("AI provider returned no choices")
    return choices[0]["message"]["content"]
