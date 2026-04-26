from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel

from config import SONGS_DIR
from services.index_store import find_song, load_index, resolve_under, save_index
from services.indexer import scan_song_library
from services.media_response import media_file_response
from services.resource_manager import delete_song_resource


router = APIRouter(prefix="/api/songs", tags=["songs"])


class MarkerPayload(BaseModel):
    time: float
    label: str
    version: str


@router.get("")
async def list_songs():
    songs = load_index().get("songs", [])
    return [
        {
            "id": song["id"],
            "title": song["title"],
            "artist": song.get("artist", ""),
            "versions": [version["name"] for version in song.get("versions", [])],
        }
        for song in songs
    ]


@router.get("/scan")
async def scan_songs(persist: bool = Query(False, description="是否写回索引")):
    songs = scan_song_library()
    if persist:
        index = load_index()
        index["songs"] = songs
        save_index(index)
    return {"songs": songs, "persisted": persist}


@router.get("/{song_id}")
async def get_song(song_id: str):
    song = find_song(load_index(), song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return song


@router.delete("/{song_id}")
async def delete_song(song_id: str):
    data = load_index()
    song = find_song(data, song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    try:
        songs = delete_song_resource(song)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    data["songs"] = songs
    save_index(data)
    return {"ok": True, "deleted": {"id": song_id, "title": song.get("title", "")}, "songs": songs}


def resolve_song_version(song: dict, version: str) -> dict:
    version_data = next((item for item in song.get("versions", []) if item["name"] == version), None)
    if not version_data:
        raise HTTPException(status_code=404, detail="Version not found")
    return version_data


def build_song_file_response(song: dict, relative_file: str, request: Request):
    try:
        file_path = resolve_under(SONGS_DIR, f"{song['path']}/{relative_file}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return media_file_response(file_path, request)


@router.get("/{song_id}/play")
async def play_song(request: Request, song_id: str, version: str = Query(..., description="版本名")):
    song = find_song(load_index(), song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    version_data = resolve_song_version(song, version)

    audio_file = version_data.get("files", {}).get("audio")
    if not audio_file:
        raise HTTPException(status_code=404, detail="No audio file for this version")

    return build_song_file_response(song, audio_file, request)


@router.get("/{song_id}/asset")
async def get_song_asset(request: Request, song_id: str, path: str = Query(..., description="相对歌曲目录的文件路径")):
    song = find_song(load_index(), song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")
    return build_song_file_response(song, path, request)


@router.post("/{song_id}/markers")
async def add_marker(song_id: str, marker: MarkerPayload):
    data = load_index()
    songs = data.get("songs", [])

    for idx, song in enumerate(songs):
        if song["id"] != song_id:
            continue

        new_marker = {
            "time": marker.time,
            "label": marker.label.strip(),
            "version": marker.version,
        }
        song.setdefault("markers", []).append(new_marker)
        data["songs"][idx] = song
        save_index(data)
        return {"ok": True, "marker": new_marker}

    raise HTTPException(status_code=404, detail="Song not found")
