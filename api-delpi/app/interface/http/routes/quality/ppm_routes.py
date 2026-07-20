"""Rotas HTTP de PPM e quantidade produzida (CT inspeção final)."""

from typing import Literal, Optional

from fastapi import APIRouter, Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    GRANULARITY_QUERY_MONTH,
)
from delpi_auth.authorization import require_any_permission

from app.application.dto.ppm.list_ppm_request import ListPpmRequest
from app.application.dto.ppm.produced_quantity_request import ProducedQuantityRequest
from app.application.dto.ppm.ppm_series_request import PpmSeriesRequest
from app.application.dto.ppm.ppm_summary_request import PpmSummaryRequest
from app.application.security.api_delpi_permissions import KPI_QUALITY_ACCESS
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.quality_composer import (
    build_get_ppm_series_use_case,
    build_get_ppm_summary_use_case,
    build_get_produced_quantity_use_case,
    build_list_ppm_use_case,
)
from app.core.responses import error_response
from app.domain.services.quality.ppm_product_scope import (
    COMPONENTS_FINISHED_PRODUCT_PREFIX,
    PLUGS_FINISHED_PRODUCT_PREFIX,
    normalize_ppm_product_prefix,
)
from app.interface.http.kpi_field_labels import (
    QUALITY_PPM_FIELD_LABELS,
    QUALITY_PRODUCED_QUANTITY_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.utils.logger import log_error

router = APIRouter(tags=["Qualidade — PPM"])

PpmType = Literal["internal", "external"]

_PPM_GOAL_KEYS = {
    "internal": goal_keys.QUALITY_PPM_INTERNAL,
    "external": goal_keys.QUALITY_PPM_EXTERNAL,
}

_PPM_PLUGS_GOAL_KEYS = {
    "internal": goal_keys.QUALITY_PPM_INTERNAL_PLUGS,
    "external": goal_keys.QUALITY_PPM_EXTERNAL_PLUGS,
}

_PPM_COMPONENTS_GOAL_KEYS = {
    "internal": goal_keys.QUALITY_PPM_INTERNAL_COMPONENTS,
    "external": goal_keys.QUALITY_PPM_EXTERNAL_COMPONENTS,
}

_PPM_PREFIX_GOAL_KEYS = {
    PLUGS_FINISHED_PRODUCT_PREFIX: _PPM_PLUGS_GOAL_KEYS,
    COMPONENTS_FINISHED_PRODUCT_PREFIX: _PPM_COMPONENTS_GOAL_KEYS,
}


def _resolve_ppm_goal_key(ppm_type: PpmType, product_prefix: str | None) -> str:
    scoped_keys = _PPM_PREFIX_GOAL_KEYS.get(product_prefix or "")
    if scoped_keys is not None:
        return scoped_keys[ppm_type]
    return _PPM_GOAL_KEYS[ppm_type]


def _parse_product_prefix(product_prefix: str | None) -> tuple[str | None, str | None]:
    if product_prefix is None:
        return None, None

    try:
        return normalize_ppm_product_prefix(product_prefix), None
    except ValueError as exc:
        return None, str(exc)


def _ppm_summary_response(
    *,
    ppm_type: PpmType,
    branch: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    product_prefix: Optional[str],
):
    normalized_prefix, prefix_error = _parse_product_prefix(product_prefix)
    if prefix_error:
        return error_response(prefix_error, status_code=400)

    try:
        dto = PpmSummaryRequest(
            type=ppm_type,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            product_prefix=normalized_prefix,
        )
        use_case = build_get_ppm_summary_use_case()
        result = enrich_dashboard_metric(
            use_case.execute(dto).to_dict(),
            source_key=_resolve_ppm_goal_key(ppm_type, normalized_prefix),
            start_date=date_start,
            end_date=date_end,
            branch=branch,
        )
        return api_delpi_success(
            result,
            operation_id=f"get_ppm_{ppm_type}_summary",
            fields=kpi_fields(QUALITY_PPM_FIELD_LABELS),
        )
    except Exception as exc:
        log_error(f"Erro ao buscar resumo de PPM {ppm_type}: {exc}")
        return error_response(
            f"Erro interno ao buscar resumo de PPM {ppm_type}.",
            status_code=500,
        )


def _ppm_list_response(
    *,
    ppm_type: PpmType,
    branch: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    page: Optional[int],
    page_size: Optional[int],
    product_prefix: Optional[str],
):
    normalized_prefix, prefix_error = _parse_product_prefix(product_prefix)
    if prefix_error:
        return error_response(prefix_error, status_code=400)

    try:
        dto = ListPpmRequest(
            type=ppm_type,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            page=page,
            page_size=page_size,
            product_prefix=normalized_prefix,
        )
        use_case = build_list_ppm_use_case()
        result = use_case.execute(dto)
        return api_delpi_success(
            result.to_dict(),
            operation_id=f"list_ppm_{ppm_type}",
        )
    except Exception as exc:
        log_error(f"Erro ao listar PPM {ppm_type}: {exc}")
        return error_response(
            f"Erro interno ao listar PPM {ppm_type}.",
            status_code=500,
        )


def _ppm_series_response(
    *,
    ppm_type: PpmType,
    granularity: str,
    branch: Optional[str],
    date_start: Optional[str],
    date_end: Optional[str],
    product_prefix: Optional[str],
):
    normalized_prefix, prefix_error = _parse_product_prefix(product_prefix)
    if prefix_error:
        return error_response(prefix_error, status_code=400)

    try:
        dto = PpmSeriesRequest(
            type=ppm_type,
            granularity=granularity,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
            product_prefix=normalized_prefix,
        )
        use_case = build_get_ppm_series_use_case()
        result = use_case.execute(dto)
        return api_delpi_success(
            result.to_dict(),
            operation_id=f"get_ppm_{ppm_type}_series",
        )
    except Exception as exc:
        log_error(f"Erro ao buscar série de PPM {ppm_type}: {exc}")
        return error_response(
            f"Erro interno ao buscar série de PPM {ppm_type}.",
            status_code=500,
        )


@router.get("/ppm/internal/summary", operation_id="get_ppm_internal_summary")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_internal_ppm_summary(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    product_prefix: Optional[str] = Query(
        None,
        description="Prefixo do código do produto (QI2_ITEM) para filtrar devoluções; produção permanece geral",
    ),
):
    return _ppm_summary_response(
        ppm_type="internal",
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        product_prefix=product_prefix,
    )


@router.get("/ppm/external/summary", operation_id="get_ppm_external_summary")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_external_ppm_summary(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    product_prefix: Optional[str] = Query(
        None,
        description="Prefixo do código do produto (QI2_ITEM) para filtrar devoluções; produção permanece geral",
    ),
):
    return _ppm_summary_response(
        ppm_type="external",
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        product_prefix=product_prefix,
    )


@router.get("/ppm/internal/series", operation_id="get_ppm_internal_series")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_internal_ppm_series(
    granularity: str = GRANULARITY_QUERY_MONTH(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    product_prefix: Optional[str] = Query(
        None,
        description="Prefixo do código do produto (QI2_ITEM) para filtrar devoluções; produção permanece geral",
    ),
):
    return _ppm_series_response(
        ppm_type="internal",
        granularity=granularity,
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        product_prefix=product_prefix,
    )


@router.get("/ppm/external/series", operation_id="get_ppm_external_series")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_external_ppm_series(
    granularity: str = GRANULARITY_QUERY_MONTH(),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    product_prefix: Optional[str] = Query(
        None,
        description="Prefixo do código do produto (QI2_ITEM) para filtrar devoluções; produção permanece geral",
    ),
):
    return _ppm_series_response(
        ppm_type="external",
        granularity=granularity,
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        product_prefix=product_prefix,
    )


@router.get("/ppm/internal", operation_id="list_ppm_internal")
@require_any_permission(KPI_QUALITY_ACCESS)
def list_internal_ppm(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
    product_prefix: Optional[str] = Query(
        None,
        description="Prefixo do código do produto (QI2_ITEM) para filtrar devoluções; produção permanece geral",
    ),
):
    return _ppm_list_response(
        ppm_type="internal",
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        page=page,
        page_size=page_size,
        product_prefix=product_prefix,
    )


@router.get("/ppm/external", operation_id="list_ppm_external")
@require_any_permission(KPI_QUALITY_ACCESS)
def list_external_ppm(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    page: int = Query(None, ge=1),
    page_size: int = Query(None, ge=1),
    product_prefix: Optional[str] = Query(
        None,
        description="Prefixo do código do produto (QI2_ITEM) para filtrar devoluções; produção permanece geral",
    ),
):
    return _ppm_list_response(
        ppm_type="external",
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        page=page,
        page_size=page_size,
        product_prefix=product_prefix,
    )


@router.get("/produced-quantity", operation_id="get_produced_quantity")
@require_any_permission(KPI_QUALITY_ACCESS)
def get_produced_quantity(
    product: list[str] = Query(
        ...,
        description="Código(s) do produto; repetível ou separado por vírgula",
    ),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
):
    try:
        dto = ProducedQuantityRequest(
            products=product,
            branch=branch,
            date_start=date_start,
            date_end=date_end,
        )
        use_case = build_get_produced_quantity_use_case()
        result = use_case.execute(dto)
        return api_delpi_success(
            result.to_dict(),
            operation_id="get_produced_quantity",
            fields=kpi_fields(QUALITY_PRODUCED_QUANTITY_FIELD_LABELS),
        )
    except ValueError as exc:
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao buscar quantidade produzida: {exc}")
        return error_response(
            "Erro interno ao buscar quantidade produzida.",
            status_code=500,
        )
