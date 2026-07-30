from __future__ import annotations

import re
from pathlib import Path

from fastapi.responses import Response, StreamingResponse

from tv_app.application.services.media_storage_service import iter_file_range

_RANGE_RE = re.compile(r"bytes=(\d*)-(\d*)", re.IGNORECASE)


def build_media_file_response(
    *,
    path: Path,
    mime_type: str,
    range_header: str | None = None,
    cache_control: str = "public, max-age=86400",
) -> Response:
    """Serve arquivo com suporte a Range (206) para seek de vídeo no browser."""
    file_size = path.stat().st_size
    base_headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": cache_control,
        "Content-Length": str(file_size),
    }

    if not range_header or not range_header.strip().lower().startswith("bytes="):
        return StreamingResponse(
            iter_file_range(path, start=0, end=file_size - 1) if file_size else iter([]),
            media_type=mime_type,
            headers=base_headers,
            status_code=200,
        )

    match = _RANGE_RE.search(range_header.strip())
    if not match or file_size <= 0:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    start_raw, end_raw = match.group(1), match.group(2)
    if not start_raw and not end_raw:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    if start_raw:
        start = int(start_raw)
        end = int(end_raw) if end_raw else file_size - 1
    else:
        # bytes=-N → últimos N bytes
        suffix = int(end_raw)
        start = max(0, file_size - suffix)
        end = file_size - 1

    if start >= file_size or end < start:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    end = min(end, file_size - 1)
    content_length = end - start + 1
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": cache_control,
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Content-Length": str(content_length),
    }
    return StreamingResponse(
        iter_file_range(path, start=start, end=end),
        media_type=mime_type,
        headers=headers,
        status_code=206,
    )
