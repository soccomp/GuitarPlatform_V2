import os
from pathlib import Path

import httpx


MINIMAX_BASE_URL = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-M2.7"
ENV_FILES = (
    Path(__file__).resolve().parents[2] / ".env",
    Path(__file__).resolve().parents[1] / ".env",
)


class AssistantConfigurationError(RuntimeError):
    pass


def ensure_ai_configured() -> None:
    if not get_minimax_api_key():
        raise AssistantConfigurationError("还没有配置 MiniMax API Key。请在 backend/.env 里添加 MINIMAX_API_KEY=你的key，然后重启平台。")


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
    api_key = get_minimax_api_key()
    if not api_key:
        raise AssistantConfigurationError("还没有配置 MiniMax API Key。请在 backend/.env 里添加 MINIMAX_API_KEY=你的key，然后重启平台。")

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            MINIMAX_BASE_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
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


def get_minimax_api_key() -> str:
    env_key = os.environ.get("MINIMAX_API_KEY", "").strip()
    if env_key:
        return env_key

    for env_file in ENV_FILES:
        key = read_env_value(env_file, "MINIMAX_API_KEY")
        if key:
            return key
    return ""


def read_env_value(env_file: Path, name: str) -> str:
    if not env_file.exists():
        return ""

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key.strip() != name:
            continue
        return value.strip().strip('"').strip("'")
    return ""
