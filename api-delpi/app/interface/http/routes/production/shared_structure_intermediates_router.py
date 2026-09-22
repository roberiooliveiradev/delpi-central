"""Rotas — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from app.interface.http.pagination_query import PAGE_SIZE_QUERY

from delpi_auth.authorization import require_any_permission

from app.application.dto.production.shared_structure_intermediates_request import (
    SharedStructureIntermediatesRequest,
)
from app.application.security.api_delpi_permissions import KPI_PRODUCTION_ACCESS
from app.composition.shared_structure_intermediates_composer import (
    build_get_shared_structure_intermediates_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.domain.production.shared_structure_intermediates_scope import (
    DEFAULT_MOVEMENT_LOOKBACK_DAYS,
    MAX_MOVEMENT_LOOKBACK_DAYS,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/production/shared-structure-intermediates",
    tags=["Produção — Estrutura compartilhada"],
)

_ITEM_FIELDS = {
    "intermediate_code": {"label": "Intermediário", "type": "string"},
    "intermediate_description": {"label": "Descrição", "type": "string"},
    "intermediate_type": {"label": "Tipo", "type": "string"},
    "shared_pa_count": {"label": "PAs compartilhados", "type": "integer"},
    "finished_products": {"label": "PAs que usam", "type": "array"},
}


def _handle_errors(action: str, exc: Exception):
    if isinstance(exc, ValueError):
        log_error(f"Erro de validação ao {action}: {exc}")
        return error_response(str(exc), status_code=400)
    if isinstance(exc, DatabaseConnectionError):
        log_error(f"Erro de banco ao {action}: {exc}")
        return error_response(
            f"Erro de conexão com o banco ao {action}.",
            status_code=503,
        )
    log_error(f"Erro ao {action}: {exc}")
    return error_response(f"Erro interno ao {action}.", status_code=500)


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_shared_structure_intermediates",
        path="/production/shared-structure-intermediates",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_shared_structure_intermediates(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    movement_from: Optional[str] = Query(
        default=None,
        description="Start of movement window (YYYY-MM-DD). Default: today minus lookback_days.",
    ),
    lookback_days: int = Query(
        default=DEFAULT_MOVEMENT_LOOKBACK_DAYS,
        ge=1,
        le=MAX_MOVEMENT_LOOKBACK_DAYS,
        description="Movement lookback when movement_from is omitted.",
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = PAGE_SIZE_QUERY("page_50_200", description="Page size."),
):
    try:
        request = SharedStructureIntermediatesRequest.from_params(
            branch=branch,
            movement_from=movement_from,
            lookback_days=lookback_days,
            page=page,
            page_size=page_size,
        )
        result = build_get_shared_structure_intermediates_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_production_shared_structure_intermediates",
            message="Intermediários compartilhados buscados com sucesso.",
            fields=_ITEM_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar intermediários compartilhados", exc)
