"""Rotas — conjuntos de ordens de produção (SC2010 x estrutura SG1010)."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query
from app.interface.http.pagination_query import (
    PAGE_SIZE_QUERY,
)

from delpi_auth.authorization import require_any_permission

from app.application.dto.production.production_order_sets_request import (
    IncompleteOrderSetsRequest,
)
from app.application.security.api_delpi_permissions import KPI_PRODUCTION_ACCESS
from app.composition.production_order_sets_composer import (
    build_get_production_order_sets_incomplete_use_case,
)
from app.core.exceptions import DatabaseConnectionError
from app.core.responses import error_response
from app.domain.production.production_order_sets_scope import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.query_param_enums import BRANCH_QUERY_OPTIONAL
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(
    prefix="/production/production-order-sets",
    tags=["Produção — Conjuntos de OP"],
)

_INCOMPLETE_SET_FIELDS = {
    "set_key": {"label": "Conjunto", "type": "string"},
    "set_number": {"label": "Número", "type": "string"},
    "set_item": {"label": "Item", "type": "string"},
    "root_code": {"label": "Produto raiz", "type": "string"},
    "root_description": {"label": "Descrição do produto raiz", "type": "string"},
    "root_type": {"label": "Tipo do produto raiz", "type": "string"},
    "root_order": {"label": "OP mãe", "type": "string"},
    "due_date": {"label": "Entrega", "type": "string", "format": "date"},
    "issued_at": {"label": "Emissão", "type": "string", "format": "date"},
    "order_count": {"label": "OPs do conjunto", "type": "integer"},
    "open_order_count": {"label": "OPs em aberto", "type": "integer"},
    "expected_component_count": {"label": "Componentes esperados", "type": "integer"},
    "created_component_count": {"label": "Componentes criados", "type": "integer"},
    "missing_count": {"label": "Faltando", "type": "integer"},
    "extra_count": {"label": "Sobrando", "type": "integer"},
    "missing_components": {"label": "Componentes faltando", "type": "array"},
    "extra_components": {"label": "Componentes sobrando", "type": "array"},
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
    "/incomplete",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_order_sets_incomplete",
        path="/production/production-order-sets/incomplete",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_order_sets_incomplete(
    branch: str | None = BRANCH_QUERY_OPTIONAL(),
    issued_from: Optional[str] = Query(
        default=None,
        description=(
            "Earliest mother order issue date (C2_EMISSAO, YYYY-MM-DD). "
            "Without it the check spans every open set, including decades-old ones."
        ),
    ),
    page: int = Query(default=1, ge=1, description="Page number (1-based)."),
    page_size: int = PAGE_SIZE_QUERY("page_50_200", description="Page size."),
):
    try:
        request = IncompleteOrderSetsRequest.from_params(
            branch=branch,
            issued_from=issued_from,
            page=page,
            page_size=page_size,
        )
        result = build_get_production_order_sets_incomplete_use_case().execute(request)
        return api_delpi_success(
            result,
            operation_id="get_production_order_sets_incomplete",
            message="Conjuntos de OP incompletos buscados com sucesso.",
            fields=_INCOMPLETE_SET_FIELDS,
        )
    except Exception as exc:
        return _handle_errors("buscar conjuntos de OP incompletos", exc)
