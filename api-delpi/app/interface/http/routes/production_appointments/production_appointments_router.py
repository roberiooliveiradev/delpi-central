from __future__ import annotations

from typing import Optional

from fastapi import APIRouter

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    PRODUCTION_APPOINTMENTS_READ_PERMISSIONS,
)
from app.composition.production_appointments_composer import (
    build_get_production_appointments_series_use_case,
    build_get_production_appointments_summary_use_case,
    build_list_production_appointment_work_centers_use_case,
    build_list_production_appointments_by_op_use_case,
    build_list_production_appointments_use_case,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.routes.production_appointments.production_appointments_branch_access import (
    branch_access_error,
)
from app.interface.http.routes.production_appointments.production_appointments_route_helpers import (
    BRANCH_QUERY,
    DATE_END_QUERY,
    DATE_START_QUERY,
    GROUP_BY_QUERY,
    OP_QUERY,
    PAGE_QUERY,
    PAGE_SIZE_QUERY,
    PRODUCT_QUERY,
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
    date_start: Optional[str] = None,
    date_end: Optional[str] = None,
    work_center: Optional[str] = None,
    op: Optional[str] = None,
    product: Optional[str] = None,
    group_by: Optional[str] = None,
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
            date_start=date_start,
            date_end=date_end,
            work_center=work_center,
            op=op,
            product=product,
            group_by=group_by,
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
def list_work_centers_route(branch: str = BRANCH_QUERY):
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
    branch: str = BRANCH_QUERY,
    date_start: Optional[str] = DATE_START_QUERY,
    date_end: Optional[str] = DATE_END_QUERY,
    work_center: Optional[str] = WORK_CENTER_QUERY,
    op: Optional[str] = OP_QUERY,
    product: Optional[str] = PRODUCT_QUERY,
    page: int = PAGE_QUERY,
    page_size: int = PAGE_SIZE_QUERY,
):
    request, err = _guard_and_build(
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        work_center=work_center,
        op=op,
        product=product,
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
    branch: str = BRANCH_QUERY,
    date_start: Optional[str] = DATE_START_QUERY,
    date_end: Optional[str] = DATE_END_QUERY,
    work_center: Optional[str] = WORK_CENTER_QUERY,
    op: Optional[str] = OP_QUERY,
    product: Optional[str] = PRODUCT_QUERY,
):
    request, err = _guard_and_build(
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        work_center=work_center,
        op=op,
        product=product,
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
    branch: str = BRANCH_QUERY,
    date_start: Optional[str] = DATE_START_QUERY,
    date_end: Optional[str] = DATE_END_QUERY,
    work_center: Optional[str] = WORK_CENTER_QUERY,
    op: Optional[str] = OP_QUERY,
    product: Optional[str] = PRODUCT_QUERY,
    group_by: str = GROUP_BY_QUERY,
):
    request, err = _guard_and_build(
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        work_center=work_center,
        op=op,
        product=product,
        group_by=group_by,
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
    "/by-op",
    **OpenApiAgentMetadataBuilder.from_contract(
        "list_production_appointments_by_op",
        path="/production/appointments/by-op",
    ),
)
@require_any_permission(PRODUCTION_APPOINTMENTS_READ_PERMISSIONS)
def by_op_route(
    branch: str = BRANCH_QUERY,
    date_start: Optional[str] = DATE_START_QUERY,
    date_end: Optional[str] = DATE_END_QUERY,
    work_center: Optional[str] = WORK_CENTER_QUERY,
    op: Optional[str] = OP_QUERY,
    product: Optional[str] = PRODUCT_QUERY,
    page: int = PAGE_QUERY,
    page_size: int = PAGE_SIZE_QUERY,
):
    request, err = _guard_and_build(
        branch=branch,
        date_start=date_start,
        date_end=date_end,
        work_center=work_center,
        op=op,
        product=product,
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
