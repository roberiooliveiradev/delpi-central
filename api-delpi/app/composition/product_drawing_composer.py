from app.application.services.drawings.drawing_pdf_library_storage import DrawingPdfLibraryStorage
from app.application.use_cases.product.get_product_drawing_metadata_use_case import (
    GetProductDrawingMetadataUseCase,
)
from app.application.use_cases.product.get_product_drawing_pdf_use_case import (
    GetProductDrawingPdfUseCase,
)


def build_get_product_drawing_metadata_use_case() -> GetProductDrawingMetadataUseCase:
    return GetProductDrawingMetadataUseCase(DrawingPdfLibraryStorage())


def build_get_product_drawing_pdf_use_case() -> GetProductDrawingPdfUseCase:
    return GetProductDrawingPdfUseCase(DrawingPdfLibraryStorage())
