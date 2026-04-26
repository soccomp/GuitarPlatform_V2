import mimetypes
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, StreamingResponse


def media_file_response(path: Path, request: Request):
    media_type, _ = mimetypes.guess_type(path.name)
    media_type = media_type or "application/octet-stream"
    file_size = path.stat().st_size
    range_header = request.headers.get("range")

    if not range_header:
        return FileResponse(
            path=path,
            media_type=media_type,
            filename=path.name,
            content_disposition_type="inline",
            headers={"Accept-Ranges": "bytes"},
        )

    start, end = parse_range_header(range_header, file_size)
    length = end - start + 1

    def iter_range():
        with open(path, "rb") as handle:
            handle.seek(start)
            remaining = length
            while remaining > 0:
                chunk = handle.read(min(1024 * 1024, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    return StreamingResponse(
        iter_range(),
        status_code=206,
        media_type=media_type,
        headers={
            "Accept-Ranges": "bytes",
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Content-Length": str(length),
        },
    )


def parse_range_header(range_header: str, file_size: int) -> tuple[int, int]:
    unit, _, value = range_header.partition("=")
    if unit.strip().lower() != "bytes":
        return 0, file_size - 1

    start_text, _, end_text = value.partition("-")
    if start_text:
        start = int(start_text)
        end = int(end_text) if end_text else file_size - 1
    else:
        suffix_length = int(end_text)
        start = max(file_size - suffix_length, 0)
        end = file_size - 1

    start = max(0, min(start, file_size - 1))
    end = max(start, min(end, file_size - 1))
    return start, end
