from __future__ import annotations

from typing import Protocol

from production_control_app.domain.product_drawing_pdf import DrawingFile


class DrawingLibraryPort(Protocol):
    def resolve_pdf(self, code: str) -> DrawingFile:
        ...
