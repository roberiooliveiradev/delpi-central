from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Query
from app.interface.http.query_param_enums import SORT_DIR_QUERY
from fastapi.responses import FileResponse

from delpi_auth.authorization import require_permission

from app.application.dto.product.get_product_drawing_request import GetProductDrawingRequest
from app.application.dto.product.list_product_drawings_request import (
    ListProductDrawingsRequest,
)
from app.application.security.api_delpi_permissions import API_DELPI_ACCESS
from app.application.services.drawings.drawing_pdf_library_storage import (
    DrawingPdfLibraryStorageError,
)
from app.composition.product_drawing_composer import (
    build_get_product_drawing_metadata_use_case,
    build_get_product_drawing_pdf_use_case,
    build_list_product_drawings_use_case,
)
from app.core.responses import error_response, not_found_response
from app.interface.http.openapi_agent_metadata import (
    LIST_PRODUCT_DRAWINGS,
    PRODUCT_DRAWING_METADATA,
    PRODUCT_DRAWING_PDF,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.product_response_helpers import product_success
from app.utils.logger import log_error

router = APIRouter()


def _parse_optional_datetime(value: str | None) -> datetime | None:
    normalized = str(value or "").strip()
    if not normalized:
        return None

    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"

    return datetime.fromisoformat(normalized)


@router.get(
    "/drawings",
    **LIST_PRODUCT_DRAWINGS,
)
@require_permission(API_DELPI_ACCESS)
def list_product_drawings(
    code: Optional[str] = Query(
        default=None,
        description="Filtro por código DELPI (prefixo por padrão; use code_exact=true para match exato).",
    ),
    code_exact: bool = Query(
        default=False,
        description="Quando true, exige match exato do código informado.",
    ),
    filename: Optional[str] = Query(
        default=None,
        description="Filtro parcial pelo nome do arquivo PDF.",
    ),
    revision: Optional[str] = Query(
        default=None,
        description="Filtro por revisão extraída do sufixo _R{NN} no filename.",
    ),
    file_kind: Optional[str] = Query(
        default=None,
        description="Tipo do arquivo: exact, revision, variant ou other.",
    ),
    has_variant: Optional[bool] = Query(
        default=None,
        description="Filtra arquivos com sufixo variante (-N).",
    ),
    has_revision: Optional[bool] = Query(
        default=None,
        description="Filtra arquivos com sufixo de revisão (_RNN).",
    ),
    modified_from: Optional[str] = Query(
        default=None,
        description="Data/hora ISO mínima de modificação do arquivo.",
    ),
    modified_to: Optional[str] = Query(
        default=None,
        description="Data/hora ISO máxima de modificação do arquivo.",
    ),
    min_size_bytes: Optional[int] = Query(default=None, ge=0),
    max_size_bytes: Optional[int] = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(
        default="product_code",
        description="product_code, filename, modified_at, size_bytes, revision ou file_kind.",
    ),
    direction: str = SORT_DIR_QUERY(),
):
    try:
        dto = ListProductDrawingsRequest(
            code=code,
            code_exact=code_exact,
            filename=filename,
            revision=revision,
            file_kind=file_kind,
            has_variant=has_variant,
            has_revision=has_revision,
            modified_from=_parse_optional_datetime(modified_from),
            modified_to=_parse_optional_datetime(modified_to),
            min_size_bytes=min_size_bytes,
            max_size_bytes=max_size_bytes,
            page=page,
            page_size=page_size,
            sort=sort,
            direction=direction,
        )
        use_case = build_list_product_drawings_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="list_product_drawings",
            message="Catálogo de desenhos PDF carregado com sucesso.",
        )
    except DrawingPdfLibraryStorageError as exc:
        return error_response(str(exc), status_code=422)
    except ValueError as exc:
        return error_response(str(exc), status_code=422)
    except Exception as exc:
        log_error(f"Erro ao listar catálogo de desenhos PDF: {exc}")
        return error_response("Erro interno ao listar desenhos PDF.", status_code=500)


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
