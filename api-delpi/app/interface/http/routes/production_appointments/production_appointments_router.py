from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    PRODUCTION_APPOINTMENTS_READ_PERMISSIONS,
)
from app.composition.production_appointments_composer import (
    build_get_production_appointments_finished_ops_series_use_case,
    build_get_production_appointments_series_use_case,
    build_get_production_appointments_summary_use_case,
    build_get_produced_quantity_use_case,
    build_list_production_appointment_work_centers_use_case,
    build_list_production_appointments_by_op_use_case,
    build_list_production_appointments_child_ops_use_case,
    build_list_production_appointments_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.interface.http.routes.production_appointments.production_appointments_branch_access import (
    branch_access_error,
)
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.routes.production_appointments.production_appointments_route_helpers import (
    BRANCH_QUERY,
    FINISHED_OPS_GRANULARITY_QUERY,
    SERIES_GRANULARITY_QUERY,
    GROUP_BY_QUERY,
    MOTHER_OP_QUERY,
    OP_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    PRODUCT_QUERY,
    SEARCH_QUERY,
    WORK_CENTER_QUERY,
    build_query_request,
    execute_route,
)
from app.utils.logger import log_error

router = APIRouter(
    prefix="/production/appointments",
    tags=["Produção — Apontamento de Produção"],
)


def _guard_and_build(
    *,
    branch: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    work_center: Optional[str] = None,
    op: Optional[str] = None,
    product: Optional[str] = None,
    search: Optional[str] = None,
    mother_op: bool = False,
    group_by: Optional[str] = None,
    granularity: Optional[str] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
    error_context: str,
):
    branch_error = branch_access_error(branch)
    if branch_error:
        return None, branch_error
    try:
        request = build_query_request(
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            work_center=work_center,
            op=op,
            product=product,
            search=search,
            mother_op=mother_op,
            group_by=group_by,
            granularity=granularity,
            page=page,
            page_size=page_size,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao {error_context}: {exc}")
        return None, error_response(str(exc), status_code=400)
    return request, None


@router.get(
    "/work-centers",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_production_appointment_work_centers",
        path="/production/appointments/work-centers",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def list_work_centers_route(branch: str = BRANCH_QUERY()):
    request, err = _guard_and_build(branch=branch, error_context="listar centros de trabalho")
    if err:
        return err
    return execute_route(
        use_case_builder=build_list_production_appointment_work_centers_use_case,
        request=request,
        operation_id="list_production_appointment_work_centers",
        success_message="Centros de trabalho carregados com sucesso.",
        error_context="listar centros de trabalho",
    )


@router.get(
    "",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_production_appointments",
        path="/production/appointments",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def list_appointments_route(
    branch: str = BRANCH_QUERY(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    work_center: Optional[str] = WORK_CENTER_QUERY(),
    op: Optional[str] = OP_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    search: Optional[str] = SEARCH_QUERY(),
    mother_op: bool = MOTHER_OP_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    request, err = _guard_and_build(
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        work_center=work_center,
        op=op,
        product=product,
        search=search,
        mother_op=mother_op,
        page=page,
        page_size=page_size,
        error_context="listar apontamentos",
    )
    if err:
        return err
    return execute_route(
        use_case_builder=build_list_production_appointments_use_case,
        request=request,
        operation_id="list_production_appointments",
        success_message="Apontamentos carregados com sucesso.",
        error_context="listar apontamentos",
    )


@router.get(
    "/summary",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_appointments_summary",
        path="/production/appointments/summary",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def summary_route(
    branch: str = BRANCH_QUERY(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    work_center: Optional[str] = WORK_CENTER_QUERY(),
    op: Optional[str] = OP_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    mother_op: bool = MOTHER_OP_QUERY(),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    request, err = _guard_and_build(
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        work_center=work_center,
        op=op,
        product=product,
        mother_op=mother_op,
        error_context="carregar resumo de apontamentos",
    )
    if err:
        return err
    return execute_route(
        use_case_builder=build_get_production_appointments_summary_use_case,
        request=request,
        operation_id="get_production_appointments_summary",
        success_message="Resumo de apontamentos carregado com sucesso.",
        error_context="carregar resumo de apontamentos",
    )


@router.get(
    "/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_appointments_series",
        path="/production/appointments/series",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def series_route(
    branch: str = BRANCH_QUERY(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    work_center: Optional[str] = WORK_CENTER_QUERY(),
    op: Optional[str] = OP_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    mother_op: bool = MOTHER_OP_QUERY(),
    group_by: str = GROUP_BY_QUERY(),
    granularity: str = SERIES_GRANULARITY_QUERY(),
):
    """Time series of produced/lost quantities by day or month."""
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    request, err = _guard_and_build(
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        work_center=work_center,
        op=op,
        product=product,
        mother_op=mother_op,
        group_by=group_by,
        granularity=granularity,
        error_context="carregar série de apontamentos",
    )
    if err:
        return err
    return execute_route(
        use_case_builder=build_get_production_appointments_series_use_case,
        request=request,
        operation_id="get_production_appointments_series",
        success_message="Série de apontamentos carregada com sucesso.",
        error_context="carregar série de apontamentos",
    )


@router.get(
    "/finished-ops/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_appointments_finished_ops_series",
        path="/production/appointments/finished-ops/series",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def finished_ops_series_route(
    branch: str = BRANCH_QUERY(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    mother_op: bool = MOTHER_OP_QUERY(),
    granularity: str = FINISHED_OPS_GRANULARITY_QUERY(),
):
    """Count of finished production orders (SC2.C2_DATRF) by day or month."""
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error
    try:
        from app.application.dto.production_appointments.finished_ops_series_query_request import (
            FinishedOpsSeriesQueryRequest,
        )

        request = FinishedOpsSeriesQueryRequest.from_query(
            branch=branch,
            date_start=start_date,
            date_end=end_date,
            product=product,
            mother_op=mother_op,
            granularity=granularity,
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar série de OPs finalizadas: {exc}")
        return error_response(str(exc), status_code=400)
    from app.interface.http.kpi_field_labels import (
        PRODUCTION_APPOINTMENTS_FINISHED_OPS_FIELD_LABELS,
        kpi_fields,
    )

    return execute_route(
        use_case_builder=build_get_production_appointments_finished_ops_series_use_case,
        request=request,
        operation_id="get_production_appointments_finished_ops_series",
        success_message="Série de OPs finalizadas carregada com sucesso.",
        error_context="carregar série de OPs finalizadas",
        fields=kpi_fields(PRODUCTION_APPOINTMENTS_FINISHED_OPS_FIELD_LABELS),
    )


@router.get(
    "/by-op",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_production_appointments_by_op",
        path="/production/appointments/by-op",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def by_op_route(
    branch: str = BRANCH_QUERY(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    work_center: Optional[str] = WORK_CENTER_QUERY(),
    op: Optional[str] = OP_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    search: Optional[str] = SEARCH_QUERY(),
    mother_op: bool = MOTHER_OP_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    request, err = _guard_and_build(
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        work_center=work_center,
        op=op,
        product=product,
        search=search,
        mother_op=mother_op,
        page=page,
        page_size=page_size,
        error_context="carregar drill-down por OP",
    )
    if err:
        return err
    return execute_route(
        use_case_builder=build_list_production_appointments_by_op_use_case,
        request=request,
        operation_id="list_production_appointments_by_op",
        success_message="Apontamentos por OP carregados com sucesso.",
        error_context="carregar drill-down por OP",
    )


@router.get(
    "/child-ops",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_production_appointments_child_ops",
        path="/production/appointments/child-ops",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def child_ops_route(
    branch: str = BRANCH_QUERY(),
    op: str = Query(..., description="Reference production order (mother or child)."),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    work_center: Optional[str] = WORK_CENTER_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    search: Optional[str] = SEARCH_QUERY(),
    page: int = PAGE_QUERY(),
    page_size: int = PAGE_SIZE_QUERY(),
):
    """Child OPs of the same family (sequence ≠ 001) with appointments in the period."""
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    request, err = _guard_and_build(
        branch=branch,
        start_date=start_date,
        end_date=end_date,
        work_center=work_center,
        op=op,
        product=product,
        search=search,
        page=page,
        page_size=page_size,
        error_context="carregar OPs filhas",
    )
    if err:
        return err
    return execute_route(
        use_case_builder=build_list_production_appointments_child_ops_use_case,
        request=request,
        operation_id="list_production_appointments_child_ops",
        success_message="OPs filhas carregadas com sucesso.",
        error_context="carregar OPs filhas",
    )


@router.get(
    "/produced-totals",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_appointments_produced_totals",
        path="/production/appointments/produced-totals",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def produced_totals_route(
    branch: str = BRANCH_QUERY(),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
    product: Optional[str] = PRODUCT_QUERY(),
    product_types: Optional[str] = Query(
        None,
        description="Comma-separated SB1 types (default PA,PI).",
    ),
):
    """Total produzido canônico: SUM(H6_QTDPROD) na inspeção final + OP mãe."""
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    branch_error = branch_access_error(branch)
    if branch_error:
        return branch_error
    try:
        from app.application.dto.production_appointments.produced_quantity_query_request import (
            ProducedQuantityQueryRequest,
        )

        tipos = None
        if product_types:
            tipos = [part.strip() for part in product_types.split(",") if part.strip()]
        query = ProducedQuantityQueryRequest.create(
            date_start=start_date,
            date_end=end_date,
            branch=branch,
            products=[product] if product else None,
            product_types=tipos,
            require_branch=True,
        )
        use_case = build_get_produced_quantity_use_case()
        result = use_case.get_totals(query)
        return api_delpi_success(
            result,
            operation_id="get_production_appointments_produced_totals",
            message="Totais de quantidade produzida carregados com sucesso.",
        )
    except ValueError as exc:
        log_error(f"Erro de validação ao carregar totais produzidos: {exc}")
        return error_response(str(exc), status_code=400)
    except Exception as exc:
        log_error(f"Erro ao carregar totais produzidos: {exc}")
        return error_response(
            "Erro interno ao carregar totais produzidos.",
            status_code=500,
        )
