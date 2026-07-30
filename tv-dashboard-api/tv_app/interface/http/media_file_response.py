from __future__ import annotations

from pathlib import Path

from fastapi.responses import FileResponse, Response


def build_media_file_response(
    *,
    path: Path,
    mime_type: str,
    range_header: str | None = None,
    cache_control: str = "public, max-age=86400",
) -> Response:
    """
    Serve arquivo para `<video>`/`<img>` com Range nativo (Starlette FileResponse).

    `filename` + `content_disposition_type=inline` evitam download forçado
    (sem `filename`, o Starlette ignora o disposition type).
    """
    del range_header  # FileResponse lê Range do ASGI scope automaticamente.
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": cache_control,
    }
    return FileResponse(
        path,
        media_type=mime_type or "application/octet-stream",
        filename=path.name,
        headers=headers,
        content_disposition_type="inline",
    )
