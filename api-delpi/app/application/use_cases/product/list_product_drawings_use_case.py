from __future__ import annotations

from app.application.dto.product.list_product_drawings_request import (
    ListProductDrawingsRequest,
)
from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorage,
)


class ListProductDrawingsUseCase:
    def __init__(self, storage: DrawingPdfLibraryStorage | None = None) -> None:
        self.storage = storage or DrawingPdfLibraryStorage()

    def execute(self, dto: ListProductDrawingsRequest) -> dict:
        return self.storage.list_catalog(
            code=dto.code,
            code_exact=dto.code_exact,
            filename=dto.filename,
            revision=dto.revision,
            file_kind=dto.file_kind,
            has_variant=dto.has_variant,
            has_revision=dto.has_revision,
            modified_from=dto.modified_from,
            modified_to=dto.modified_to,
            min_size_bytes=dto.min_size_bytes,
            max_size_bytes=dto.max_size_bytes,
            page=dto.page,
            page_size=dto.page_size,
            sort=dto.sort,
            direction=dto.direction,
        )
