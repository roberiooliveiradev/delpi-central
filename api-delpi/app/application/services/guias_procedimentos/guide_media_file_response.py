"""Resposta de arquivo com suporte a HTTP Range (vídeos / streaming parcial)."""

from __future__ import annotations

import mimetypes
from pathlib import Path

from fastapi import Request
from fastapi.responses import FileResponse, Response, StreamingResponse


def build_file_response(
    *,
    path: Path,
    request: Request | None = None,
    media_type: str | None = None,
    filename: str | None = None,
    enable_range: bool = False,
) -> Response:
    """Serve arquivo; com ``enable_range=True`` honra ``Range`` (206 Partial Content)."""
    resolved = path.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(str(resolved))

    mime = media_type or mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
    display_name = filename or resolved.name
    file_size = resolved.stat().st_size

    if not enable_range or request is None:
        return FileResponse(
            path=resolved,
            media_type=mime,
            filename=display_name,
        )

    range_header = request.headers.get("range") or request.headers.get("Range")
    if not range_header:
        response = FileResponse(
            path=resolved,
            media_type=mime,
            filename=display_name,
        )
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Content-Length"] = str(file_size)
        return response

    # bytes=start-end
    units, _, range_spec = range_header.partition("=")
    if units.strip().lower() != "bytes" or not range_spec:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    first = range_spec.split(",")[0].strip()
    start_s, _, end_s = first.partition("-")
    try:
        if start_s == "":
            # suffix: bytes=-N
            suffix_len = int(end_s)
            if suffix_len <= 0:
                raise ValueError
            start = max(file_size - suffix_len, 0)
            end = file_size - 1
        else:
            start = int(start_s)
            end = int(end_s) if end_s else file_size - 1
    except ValueError:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    if start < 0 or start >= file_size or end < start:
        return Response(status_code=416, headers={"Content-Range": f"bytes */{file_size}"})

    end = min(end, file_size - 1)
    length = end - start + 1

    def _iter_file():
        with resolved.open("rb") as handle:
            handle.seek(start)
            remaining = length
            chunk_size = 64 * 1024
            while remaining > 0:
                chunk = handle.read(min(chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "Content-Type": mime,
        "Content-Disposition": f'inline; filename="{display_name}"',
    }
    return StreamingResponse(
        _iter_file(),
        status_code=206,
        headers=headers,
        media_type=mime,
    )
