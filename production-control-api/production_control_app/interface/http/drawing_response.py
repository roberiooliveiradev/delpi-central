"""HTTP response helpers for Product Drawing PDFs."""

from __future__ import annotations

from fastapi.responses import FileResponse, Response

from production_control_app.domain.product_drawing_pdf import DrawingFile


def drawing_pdf_response(drawing: DrawingFile) -> Response:
    headers = {"Cache-Control": "no-store"}
    media = drawing.media_type or "application/pdf"
    if drawing.content is not None:
        safe_name = (drawing.filename or "drawing.pdf").replace('"', "")
        return Response(
            content=drawing.content,
            media_type=media,
            headers={
                **headers,
                "Content-Disposition": f'inline; filename="{safe_name}"',
            },
        )
    if drawing.path is None:
        raise ValueError("DrawingFile has neither content nor path")
    return FileResponse(
        drawing.path,
        media_type=media,
        filename=drawing.filename,
        content_disposition_type="inline",
        headers=headers,
    )
