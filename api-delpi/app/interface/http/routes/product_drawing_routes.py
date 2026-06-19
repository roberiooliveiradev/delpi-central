from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from delpi_auth.authorization import require_permission

from app.application.dto.product.get_product_drawing_request import GetProductDrawingRequest
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorageError,
)
from app.composition.product_drawing_composer import (
    build_get_product_drawing_metadata_use_case,
    build_get_product_drawing_pdf_use_case,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.openapi_agent_metadata import (
    PRODUCT_DRAWING_METADATA,
    PRODUCT_DRAWING_PDF,
)
from app.interface.http.routes.product_response_helpers import product_success
from app.utils.logger import log_error

router = APIRouter()


@router.get(
    "/{code}/drawing",
    **PRODUCT_DRAWING_METADATA,
)
@require_permission(API_DELPI_ACCESS)
def get_product_drawing_metadata(code: str):
    try:
        dto = GetProductDrawingRequest(code=code)
        use_case = build_get_product_drawing_metadata_use_case()
        result = use_case.execute(dto)

        if not result.get("found"):
            return not_found_response(
                result.get("message") or "Desenho PDF não encontrado para o produto informado."
            )

        return product_success(
            result,
            operation_id="get_product_drawing",
            entity="product_drawing",
            shape="scalar",
            code=code,
            message="Metadados do desenho PDF carregados com sucesso.",
        )
    except DrawingPdfLibraryStorageError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao buscar metadados do desenho do produto {code}: {exc}")
        return error_response("Erro interno ao buscar desenho do produto.", status_code=500)


@router.get(
    "/{code}/drawing/pdf",
    **PRODUCT_DRAWING_PDF,
)
@require_permission(API_DELPI_ACCESS)
def get_product_drawing_pdf(code: str):
    try:
        dto = GetProductDrawingRequest(code=code)
        use_case = build_get_product_drawing_pdf_use_case()
        file_path, filename = use_case.execute(dto)
        return FileResponse(
            path=file_path,
            media_type="application/pdf",
            filename=filename,
            content_disposition_type="inline",
        )
    except DrawingPdfLibraryStorageError as exc:
        return not_found_response(str(exc))
    except Exception as exc:
        log_error(f"Erro ao baixar desenho PDF do produto {code}: {exc}")
        return error_response("Erro interno ao baixar desenho do produto.", status_code=500)
