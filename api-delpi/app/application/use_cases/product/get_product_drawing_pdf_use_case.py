from __future__ import annotations

from pathlib import Path

from app.application.dto.product.get_product_drawing_request import GetProductDrawingRequest
from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
    DrawingPdfLibraryStorageError,
)


class GetProductDrawingPdfUseCase:
    def __init__(self, storage: DrawingPdfLibraryStorage | None = None) -> None:
        self.storage = storage or DrawingPdfLibraryStorage()

    def execute(self, dto: GetProductDrawingRequest) -> tuple[Path, str]:
        try:
            path = self.storage.resolve_pdf_path(dto.code)
        except DrawingPdfLibraryStorageError as exc:
            raise DrawingPdfLibraryStorageError(str(exc)) from exc
        return path, path.name
