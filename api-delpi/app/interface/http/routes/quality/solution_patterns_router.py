from __future__ import annotations

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import QUALITY_ACTION_PLANS_READ_PERMISSIONS
from app.composition.quality_intelligence_composer import build_list_solution_patterns_use_case
from app.core.responses import error_response
from app.infrastructure.persistence.plugins.plugin_base_repository import PluginsRepositoryError
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

router = APIRouter(prefix="/solution-patterns", tags=["PAC Qualidade — padrões de solução"])

_SOLUTION_PATTERNS_BASE = "/quality/solution-patterns"


def _solution_patterns_openapi(operation_id: str, subpath: str = "") -> dict:
    return OpenApiAgentMetadataBuilder.from_contract(
        operation_id,
        path=f"{_SOLUTION_PATTERNS_BASE}{subpath}",
    )


@router.get("", **_solution_patterns_openapi("list_quality_solution_patterns"))
@require_any_permission(QUALITY_ACTION_PLANS_READ_PERMISSIONS)
def list_solution_patterns(
    problem_category: str | None = Query(default=None),
    failure_mode: str | None = Query(default=None),
    q: str | None = Query(default=None, description="Busca em título, categoria e modo de falha"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    try:
        return api_delpi_success(
            build_list_solution_patterns_use_case().execute(
                problem_category=problem_category,
                failure_mode=failure_mode,
                q=q,
                page=page,
                page_size=page_size,
            ),
            operation_id="list_quality_solution_patterns",
        )
    except PluginsRepositoryError as exc:
        log_error(f"Erro ao listar padrões de solução PAC: {exc}")
        return error_response("Erro ao listar padrões de solução.", status_code=500)
