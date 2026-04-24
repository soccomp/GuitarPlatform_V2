from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
import json
import os
import re
from pathlib import Path
from typing import Optional

router = APIRouter(prefix="/api/songs", tags=["songs"])

DATA_DIR = Path(__file__).parent.parent / "data"
LIBRARY_DIR = Path(__file__).parent.parent.parent / "library" / "songs"
INDEX_FILE = DATA_DIR / "index.json"


def load_index() -> dict:
    if INDEX_FILE.exists():
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"songs": [], "courses": [], "videos": []}


def save_index(data: dict) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


@router.get("")
async def list_songs():
    """返回所有歌曲摘要列表"""
    data = load_index()
    songs = data.get("songs", [])
    return [
        {
            "id": s["id"],
            "title": s["title"],
            "artist": s.get("artist", ""),
            "versions": [v["name"] for v in s.get("versions", [])]
        }
        for s in songs
    ]


@router.get("/scan")
async def scan_songs():
    """
    扫描 library/songs 目录，识别所有歌曲和版本。
    按子目录分组，每个子目录为一个版本。
    支持格式：.gp5, .gp, .pdf, .mp3
    返回扫描结果（不自动写回 index.json）
    """
    if not LIBRARY_DIR.exists():
        return {"songs": []}

    songs_map = {}
    audio_extensions = {".mp3", ".wav", ".flac", ".m4a"}
    score_extensions = {".gp5", ".gp", ".pdf", ".gpzip"}

    for item in LIBRARY_DIR.iterdir():
        if item.is_dir():
            # 顶级目录作为歌曲
            song_path = item
            versions = []

            for subitem in song_path.iterdir():
                if subitem.is_dir():
                    # 子目录作为版本
                    version_name = subitem.name
                    files = {"gp": None, "pdf": None, "audio": None}

                    for f in subitem.iterdir():
                        ext = f.suffix.lower()
                        if ext in audio_extensions and files["audio"] is None:
                            files["audio"] = f.name
                        elif ext in score_extensions:
                            if ext in {".gp5", ".gp", ".gpzip"} and files["gp"] is None:
                                files["gp"] = f.name
                            elif ext == ".pdf" and files["pdf"] is None:
                                files["pdf"] = f.name

                    # 也要检查版本目录下有没有根级文件
                    for f in song_path.glob("*"):
                        if f.is_file() and f.suffix.lower() not in {".gitkeep"}:
                            ext = f.suffix.lower()
                            if ext in audio_extensions and files["audio"] is None:
                                files["audio"] = f.name
                            elif ext in score_extensions:
                                if ext in {".gp5", ".gp", ".gpzip"} and files["gp"] is None:
                                    files["gp"] = f.name
                                elif ext == ".pdf" and files["pdf"] is None:
                                    files["pdf"] = f.name

                    if any(files.values()):
                        versions.append({"name": version_name, "files": {k: v for k, v in files.items() if v}})

            # 如果顶级目录有文件但没有版本目录，把顶级目录当作默认版本
            if not versions:
                files = {"gp": None, "pdf": None, "audio": None}
                for f in song_path.iterdir():
                    if f.is_file():
                        ext = f.suffix.lower()
                        if ext in audio_extensions and files["audio"] is None:
                            files["audio"] = f.name
                        elif ext in score_extensions:
                            if ext in {".gp5", ".gp", ".gpzip"} and files["gp"] is None:
                                files["gp"] = f.name
                            elif ext == ".pdf" and files["pdf"] is None:
                                files["pdf"] = f.name
                if any(files.values()):
                    versions.append({"name": "默认版", "files": {k: v for k, v in files.items() if v}})

            if versions:
                songs_map[song_path.name] = {
                    "title": song_path.name,
                    "path": f"songs/{song_path.name}/",
                    "versions": versions
                }

    return {"songs": list(songs_map.values())}


@router.get("/{song_id}")
async def get_song(song_id: str):
    """返回指定歌曲的完整详情"""
    data = load_index()
    for s in data.get("songs", []):
        if s["id"] == song_id:
            return s
    raise HTTPException(status_code=404, detail="Song not found")


@router.get("/{song_id}/play")
async def play_song(song_id: str, version: str = Query(..., description="版本名")):
    """流式播放指定版本的伴奏音频"""
    data = load_index()
    song = None
    for s in data.get("songs", []):
        if s["id"] == song_id:
            song = s
            break

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # 找到对应版本
    version_data = None
    for v in song.get("versions", []):
        if v["name"] == version:
            version_data = v
            break

    if not version_data:
        raise HTTPException(status_code=404, detail="Version not found")

    audio_file = version_data.get("files", {}).get("audio")
    if not audio_file:
        raise HTTPException(status_code=404, detail="No audio file for this version")

    audio_path = LIBRARY_DIR / song["path"] / version / audio_file if version != "默认版" else LIBRARY_DIR / song["path"] / audio_file

    # 如果找不到，尝试直接在歌曲目录下找
    if not audio_path.exists():
        audio_path = LIBRARY_DIR / song["path"] / audio_file

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    def iterfile():
        with open(audio_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'inline; filename="{audio_file}"'}
    )


@router.post("/{song_id}/markers")
async def add_marker(song_id: str, marker: dict):
    """为歌曲添加打点标记"""
    data = load_index()

    # 找到歌曲
    song = None
    song_idx = None
    for i, s in enumerate(data.get("songs", [])):
        if s["id"] == song_id:
            song = s
            song_idx = i
            break

    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    # 初始化 markers 列表
    if "markers" not in song:
        song["markers"] = []

    # 添加新标记
    new_marker = {
        "time": marker.get("time"),
        "label": marker.get("label", ""),
        "version": marker.get("version", "")
    }
    song["markers"].append(new_marker)

    # 保存回 index
    data["songs"][song_idx] = song
    save_index(data)

    return {"ok": True, "marker": new_marker}
