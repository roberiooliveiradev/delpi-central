from __future__ import annotations

from app.application.dto.product.get_product_drawing_request import GetProductDrawingRequest
from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
    DrawingPdfLibraryStorageError,
)


class GetProductDrawingMetadataUseCase:
    def __init__(self, storage: DrawingPdfLibraryStorage | None = None) -> None:
        self.storage = storage or DrawingPdfLibraryStorage()

    def execute(self, dto: GetProductDrawingRequest) -> dict:
        try:
            match = self.storage.find_drawing(dto.code)
        except DrawingPdfLibraryStorageError as exc:
            return {
                "found": False,
                "product_code": dto.code,
                "message": str(exc),
            }

        if match is None:
            return {
                "found": False,
                "product_code": dto.code.strip().upper(),
                "message": "Desenho PDF não encontrado para o produto informado.",
            }

        return match.to_metadata_dict()
