from fastapi import APIRouter, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json
import os
from pathlib import Path
import httpx

router = APIRouter(prefix="/api/courses", tags=["courses"])

DATA_DIR = Path(__file__).parent.parent / "data"
INDEX_FILE = DATA_DIR / "index.json"
LIBRARY_DIR = DATA_DIR.parent / "library"

MINIMAX_API_KEY = os.environ.get(
    "MINIMAX_API_KEY",
    "sk-cp-HLBJfaOReObTJACaUdZ9k1ZaEy5CwKtKjuS9dXWHYwOudeXAxEKbmaeNVQR8DDMhxYM85z42SWC0PBBmXYZOE9_YT7MKRIVr0ecNBHV-VAEjfCi4UOGO544"
)
MINIMAX_BASE_URL = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
MINIMAX_MODEL = "MiniMax-M2.7"


def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"courses": []}


# ─── Request/Response Models ──────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    transcript: str


class AskResponse(BaseModel):
    answer: str


class PracticeRequest(BaseModel):
    topic: str
    level: str = "入门"  # 入门 / 进阶 / 高级


class PracticeResponse(BaseModel):
    tasks: list[str]
    tips: str


# ─── Course CRUD ─────────────────────────────────────────────────────────────

@router.get("")
async def list_courses():
    data = load_index()
    courses = data.get("courses", [])
    return [
        {"id": c["id"], "title": c["title"], "description": c.get("description", "")}
        for c in courses
    ]


@router.get("/{course_id}")
async def get_course(course_id: str):
    data = load_index()
    courses = data.get("courses", [])
    for c in courses:
        if c["id"] == course_id:
            return c
    raise HTTPException(status_code=404, detail="Course not found")


@router.get("/{course_id}/transcript")
async def get_transcript(course_id: str):
    data = load_index()
    courses = data.get("courses", [])
    for c in courses:
        if c["id"] == course_id:
            transcript_path = c.get("transcript_path")
            if not transcript_path:
                return {"content": ""}
            full_path = LIBRARY_DIR / "courses" / transcript_path
            if full_path.exists():
                with open(full_path, "r", encoding="utf-8") as f:
                    return {"content": f.read()}
            return {"content": ""}
    raise HTTPException(status_code=404, detail="Course not found")


# ─── Video Streaming ─────────────────────────────────────────────────────────

@router.get("/{course_id}/stream")
async def stream_video(course_id: str):
    """Redirect to video file URL for HLS/jwplayer progressive download."""
    data = load_index()
    courses = data.get("courses", [])
    for c in courses:
        if c["id"] == course_id:
            video_path = c.get("video_path")
            if not video_path:
                raise HTTPException(status_code=404, detail="No video for this course")
            full_path = LIBRARY_DIR / "courses" / video_path
            if not full_path.exists():
                raise HTTPException(status_code=404, detail="Video file not found")
            # Return the file path for the frontend to consume via /library alias
            return {"url": f"/library/courses/{video_path}"}
    raise HTTPException(status_code=404, detail="Course not found")


# ─── 小霞 Q&A ─────────────────────────────────────────────────────────────────

@router.post("/{course_id}/ask", response_model=AskResponse)
async def ask_course(course_id: str, body: AskRequest):
    """
    基于课程 transcript 回答用户提问。
    小霞扮演吉他助教角色，用中文回答。
    """
    data = load_index()
    courses = data.get("courses", [])
    course = next((c for c in courses if c["id"] == course_id), None)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    transcript = body.transcript or ""

    system_prompt = (
        "你叫小霞，是哥的专属吉他学习助教。\n"
        "用户正在学习课程：《" + course.get("title", "") + "》。\n"
        "以下是这门课的笔记/录音转写内容：\n"
        + (transcript[:3000] if transcript else "(暂无笔记内容)") +
        "\n\n请基于以上内容，用中文回答用户的问题。\n"
        "回答要专业、温暖、有耐心，适当引用课程内容中的原话或具体知识点。\n"
        "如果用户的问题超出课程内容范围，可以基于你自己的吉他知识回答，但要说明。"
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            MINIMAX_BASE_URL,
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MINIMAX_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": body.question},
                ],
                "temperature": 0.7,
                "max_tokens": 600,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"MiniMax API error: {resp.text}")
        result = resp.json()
        choices = result.get("choices", [])
        if not choices:
            raise HTTPException(status_code=502, detail="No response from model")
        answer = choices[0]["message"]["content"]
        return AskResponse(answer=answer)


# ─── 小霞陪练 ─────────────────────────────────────────────────────────────────

@router.post("/generate-practice", response_model=PracticeResponse)
async def generate_practice(body: PracticeRequest):
    """
    根据课程主题生成练习任务。
    小霞扮演陪练角色，生成循序渐进的练习清单。
    """
    system_prompt = (
        "你叫小霞，是哥的专属吉他陪练助教。\n"
        "根据以下课程主题和难度等级，为用户生成每日练习任务清单。\n"
        "要求：\n"
        "1. 生成5-8个循序渐进的练习任务\n"
        "2. 每个任务说明练什么、怎么练、练到什么程度算合格\n"
        "3. 最后给3条实用练习小贴士\n"
        "4. 用中文回答，格式清晰，用 emoji 分隔\n"
        "5. 难度等级：入门 / 进阶 / 高级"
    )

    user_content = f"课程主题：{body.topic}\n难度等级：{body.level}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            MINIMAX_BASE_URL,
            headers={
                "Authorization": f"Bearer {MINIMAX_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MINIMAX_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                "temperature": 0.8,
                "max_tokens": 800,
            },
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"MiniMax API error: {resp.text}")
        result = resp.json()
        choices = result.get("choices", [])
        if not choices:
            raise HTTPException(status_code=502, detail="No response from model")

        content = choices[0]["message"]["content"]
        # 简单解析：按行分割，tasks 是每行开头的练习项，tips 是最后的贴士
        lines = content.split("\n")
        tasks = [l.lstrip("0123456789.📋🎸 ").strip() for l in lines if l.strip()]
        return PracticeResponse(tasks=tasks, tips="\n".join(lines[-3:]) if len(lines) > 3 else "")
