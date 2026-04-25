from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import SONGS_DIR
from services.index_store import find_song, load_index, resolve_under, save_index
from services.indexer import scan_song_library


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


@router.get("/{song_id}/play")
async def play_song(song_id: str, version: str = Query(..., description="版本名")):
    song = find_song(load_index(), song_id)
    if not song:
        raise HTTPException(status_code=404, detail="Song not found")

    version_data = next((item for item in song.get("versions", []) if item["name"] == version), None)
    if not version_data:
        raise HTTPException(status_code=404, detail="Version not found")

    audio_file = version_data.get("files", {}).get("audio")
    if not audio_file:
        raise HTTPException(status_code=404, detail="No audio file for this version")

    try:
        audio_path = resolve_under(SONGS_DIR, f"{song['path']}/{audio_file}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")

    def iterfile():
        with open(audio_path, "rb") as handle:
            while chunk := handle.read(8192):
                yield chunk

    return StreamingResponse(
        iterfile(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'inline; filename="{audio_file}"'},
    )


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
