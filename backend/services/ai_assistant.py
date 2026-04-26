import os
from pathlib import Path

import httpx


DEFAULT_MINIMAX_BASE_URL = "https://api.minimaxi.com/anthropic/v1/messages"
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
        "system": system_prompt,
        "messages": [{"role": "user", "content": question}],
        "temperature": 0.7,
        "max_tokens": 700,
    }
    return await _send_chat(payload)


async def generate_practice_plan(topic: str, level: str) -> str:
    ensure_ai_configured()

    payload = {
        "model": MINIMAX_MODEL,
        "system": (
            "你叫小霞，是哥的专属吉他陪练助教。\n"
            "请根据课程主题和难度等级生成 5 到 8 个循序渐进的练习任务，"
            "并在最后附 2 到 3 条实用练习建议。"
        ),
        "messages": [
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
            get_minimax_base_url(),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    response.raise_for_status()
    result = response.json()
    provider_error = extract_provider_error(result)
    if provider_error:
        raise RuntimeError(provider_error)

    content = extract_assistant_content(result)
    if content:
        return content

    raise RuntimeError("AI provider returned no answer content")


def extract_assistant_content(result: dict) -> str:
    anthropic_content = result.get("content")
    if isinstance(anthropic_content, str):
        return anthropic_content.strip()
    if isinstance(anthropic_content, list):
        parts = []
        for item in anthropic_content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        content = "\n".join(part for part in parts if part).strip()
        if content:
            return content

    choices = result.get("choices") or []
    if not choices:
        return ""

    message = choices[0].get("message") or {}
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text") or item.get("content") or ""))
            else:
                parts.append(str(item))
        return "\n".join(part for part in parts if part).strip()
    return ""


def extract_provider_error(result: dict) -> str:
    error = result.get("error") or {}
    if error:
        return (error.get("message") or error.get("type") or str(error)).strip()

    base_resp = result.get("base_resp") or {}
    status_code = base_resp.get("status_code", 0)
    status_msg = (base_resp.get("status_msg") or "").strip()
    if status_code and status_code != 0:
        return status_msg or f"MiniMax returned status code {status_code}"

    if result.get("input_sensitive"):
        return "MiniMax 拒绝了这次输入：问题或课程内容触发了输入安全策略。"
    if result.get("output_sensitive"):
        return "MiniMax 生成结果触发了输出安全策略，没有返回可展示内容。"
    return ""


def get_minimax_base_url() -> str:
    configured_url = os.environ.get("MINIMAX_BASE_URL", "").strip()
    if configured_url:
        return configured_url

    for env_file in ENV_FILES:
        configured_url = read_env_value(env_file, "MINIMAX_BASE_URL")
        if configured_url:
            return configured_url
    return DEFAULT_MINIMAX_BASE_URL


def get_minimax_api_key() -> str:
    env_key = normalize_api_key(os.environ.get("MINIMAX_API_KEY", ""))
    if env_key:
        return env_key

    for env_file in ENV_FILES:
        key = normalize_api_key(read_env_value(env_file, "MINIMAX_API_KEY"))
        if key:
            return key
    return ""


def normalize_api_key(value: str) -> str:
    key = str(value or "").strip().strip('"').strip("'")
    if key.lower().startswith("bearer "):
        key = key[7:].strip()
    return key


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
