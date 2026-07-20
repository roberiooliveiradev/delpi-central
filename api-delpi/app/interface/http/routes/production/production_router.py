from fastapi import APIRouter, Path, Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    GRANULARITY_QUERY_REQUIRED,
    PRODUCT_TYPE_QUERY,
    SORT_DIR_QUERY,
)

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import (
    EFICIENCIA_FABRIL_ACCESS,
    KPI_PRODUCTION_ACCESS,
)
from app.core.responses import error_response
from app.interface.http.openapi_agent_metadata import (
    PRODUCTION_EFICIENCIA_FABRIL_APPOINTMENTS,
    PRODUCTION_EFICIENCIA_FABRIL_DASHBOARD,
    PRODUCTION_OEE,
    PRODUCTION_OEE_APPOINTMENT,
    PRODUCTION_OTD,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

from app.application.dto.production.production_oee_series_request import (
    ProductionOeeSeriesRequest,
)
from app.application.dto.production.production_otd_series_request import (
    ProductionOtdSeriesRequest,
)
from app.application.dto.production.get_production_oee_appointment_by_id_request import (
    GetProductionOeeAppointmentByIdRequest,
)
from app.application.dto.production.get_production_oee_request import (
    GetProductionOeeRequest,
)
from app.application.dto.production.get_production_otd_request import (
    GetProductionOtdRequest,
)
from app.application.dto.production.production_request import ProductionRequest
from app.application.dto.financial.get_rol_request import GetRolRequest

from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.production_composer import (
    build_get_direct_labor_cost_pct_use_case,
    build_get_production_cost_pct_use_case,
    build_get_depreciation_pct_use_case,
    build_get_overall_equipment_effectiveness_pct_use_case,
    build_get_production_oee_series_use_case,
    build_get_production_otd_series_use_case,
    build_get_on_time_delivery_pct_use_case,
    build_get_production_oee_appointment_by_id_use_case,
    build_get_production_oee_use_case,
    build_get_production_otd_use_case,
    build_get_eficiencia_fabril_dashboard_use_case,
    build_get_eficiencia_fabril_appointments_use_case,
)
from app.interface.http.kpi_field_labels import (
    PRODUCTION_COST_FIELD_LABELS,
    PRODUCTION_OEE_FIELD_LABELS,
    PRODUCTION_OTD_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric

router = APIRouter(prefix="/production", tags=["Produção"])


@router.get(
    "/direct_labor_cost_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_direct_labor_cost_pct",
        path="/production/direct_labor_cost_pct",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_direct_labor_cost_pct(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_direct_labor_cost_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        request_rol = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request, request_rol),
            source_key=goal_keys.PRODUCTION_DIRECT_LABOR,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_direct_labor_cost_pct",
            message="Custo de mão de obra direta buscado com sucesso.",
            fields=kpi_fields(PRODUCTION_COST_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar custo de mão de obra direta: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar custo de mão de obra direta: {exc}")
        return error_response(
            "Erro interno ao buscar custo de mão de obra direta.",
            status_code=500,
        )


@router.get(
    "/production_cost_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_cost_pct",
        path="/production/production_cost_pct",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_cost_pct(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_production_cost_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        request_rol = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request, request_rol),
            source_key=goal_keys.PRODUCTION_COST,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_production_cost_pct",
            message="Custo de produção buscado com sucesso.",
            fields=kpi_fields(PRODUCTION_COST_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar custo de produção: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar custo de produção: {exc}")
        return error_response(
            "Erro interno ao buscar custo de produção.",
            status_code=500,
        )


@router.get(
    "/depreciation_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_depreciation_pct",
        path="/production/depreciation_pct",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_depreciation_pct(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_depreciation_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        request_rol = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request, request_rol),
            source_key=goal_keys.PRODUCTION_DEPRECIATION,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_depreciation_pct",
            message="Depreciação buscada com sucesso.",
            fields=kpi_fields(PRODUCTION_COST_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar depreciação: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar depreciação: {exc}")
        return error_response(
            "Erro interno ao buscar depreciação.",
            status_code=500,
        )
    

@router.get(
    "/oee/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_oee_series",
        path="/production/oee/series",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_oee_series(
    granularity: str = GRANULARITY_QUERY_REQUIRED,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = BRANCH_QUERY_OPTIONAL,
):
    try:
        request = ProductionOeeSeriesRequest(
            granularity=granularity,
            date_start=start_date,
            date_end=end_date,
            branch=branch,
        )

        use_case = build_get_production_oee_series_use_case()
        result = use_case.execute(request)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_production_oee_series",
            message="Série temporal de OEE carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na série de OEE: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar série de OEE: {exc}")
        return error_response(
            "Erro interno ao carregar série temporal de OEE.",
            status_code=500,
        )


@router.get(
    "/otd/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_production_otd_series",
        path="/production/otd/series",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_otd_series(
    granularity: str = GRANULARITY_QUERY_REQUIRED,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    branch: str | None = BRANCH_QUERY_OPTIONAL,
):
    try:
        request = ProductionOtdSeriesRequest(
            granularity=granularity,
            date_start=start_date,
            date_end=end_date,
            branch=branch,
        )

        use_case = build_get_production_otd_series_use_case()
        result = use_case.execute(request)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_production_otd_series",
            message="Série temporal de OTD carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação na série de OTD: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar série de OTD: {exc}")
        return error_response(
            "Erro interno ao carregar série temporal de OTD.",
            status_code=500,
        )


@router.get("/otd", **PRODUCTION_OTD)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_otd(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=1000),
    sort_by: str | None = Query(default=None),
    sort_dir: str = SORT_DIR_QUERY,
):
    try:
        use_case = build_get_production_otd_use_case()

        request = GetProductionOtdRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.PRODUCTION_OTD,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_production_otd",
            message="OTD de produção carregado com sucesso.",
            fields=kpi_fields(PRODUCTION_OTD_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar OTD de produção: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar OTD de produção: {exc}")
        return error_response(
            "Erro interno ao buscar OTD de produção.",
            status_code=500,
        )


@router.get("/oee", **PRODUCTION_OEE)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_oee(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    status: str | None = Query(default=None),
    efficiency_bands: str | None = Query(
        default=None,
        description="Faixas de eficiência (csv): ok, low, verify",
    ),
    work_center: str | None = Query(
        default=None,
        description="Centro(s) de trabalho (csv)",
    ),
    production_order: str | None = Query(
        default=None,
        description="Ordem(ns) de produção (csv)",
    ),
    operator_code: str | None = Query(
        default=None,
        description="Código(s) do operador (csv)",
    ),
    product_type: str | None = PRODUCT_TYPE_QUERY,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=1000),
    sort_by: str | None = Query(default=None),
    sort_dir: str = SORT_DIR_QUERY,
):
    try:
        use_case = build_get_production_oee_use_case()

        request = GetProductionOeeRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            status=status,
            efficiency_bands=efficiency_bands,
            work_center=work_center,
            production_order=production_order,
            operator_code=operator_code,
            product_type=product_type,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.PRODUCTION_OEE,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_production_oee",
            message="OEE de produção carregado com sucesso.",
            fields=kpi_fields(PRODUCTION_OEE_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar OEE de produção: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar OEE de produção: {exc}")
        return error_response(
            "Erro interno ao buscar OEE de produção.",
            status_code=500,
        )


@router.get("/oee/appointments/{appointment_id}", **PRODUCTION_OEE_APPOINTMENT)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_production_oee_appointment_by_id(
    appointment_id: int = Path(..., ge=1),
    branch: str | None = BRANCH_QUERY_OPTIONAL,
):
    try:
        use_case = build_get_production_oee_appointment_by_id_use_case()
        result = use_case.execute(
            GetProductionOeeAppointmentByIdRequest(
                appointment_id=appointment_id,
                branch=branch,
            )
        )

        if not result:
            return error_response(
                "Apontamento de OEE não encontrado.",
                status_code=404,
            )

        return api_delpi_success(
            result,
            operation_id="get_production_oee_appointment_by_id",
            message="Detalhe do apontamento OEE carregado com sucesso.",
            entity="production_oee_appointment",
            shape="composite_analysis",
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar apontamento OEE: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar apontamento OEE: {exc}")
        return error_response(
            "Erro interno ao buscar detalhe do apontamento OEE.",
            status_code=500,
        )


@router.get(
    "/overall_equipment_effectiveness_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_overall_equipment_effectiveness_pct",
        path="/production/overall_equipment_effectiveness_pct",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_overall_equipment_effectiveness_pct(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_overall_equipment_effectiveness_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.PRODUCTION_OEE,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_overall_equipment_effectiveness_pct",
            message="Eficiência geral dos equipamentos buscada com sucesso.",
            fields=kpi_fields(PRODUCTION_OEE_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar eficiência geral dos equipamentos: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar eficiência geral dos equipamentos: {exc}")
        return error_response(
            "Erro interno ao buscar eficiência geral dos equipamentos.",
            status_code=500,
        )
    

@router.get(
    "/on_time_delivery_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_on_time_delivery_pct",
        path="/production/on_time_delivery_pct",
    ),
)
@require_any_permission(KPI_PRODUCTION_ACCESS)
def get_on_time_delivery_pct(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_on_time_delivery_pct_use_case()

        request = ProductionRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.PRODUCTION_OTD,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_on_time_delivery_pct",
            message="On-Time Delivery buscado com sucesso.",
            fields=kpi_fields(PRODUCTION_OTD_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar On-Time Delivery: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar On-Time Delivery: {exc}")
        return error_response(
            "Erro interno ao buscar On-Time Delivery.",
            status_code=500,
        )


@router.get("/eficiencia-fabril/dashboard", **PRODUCTION_EFICIENCIA_FABRIL_DASHBOARD)
@require_any_permission(EFICIENCIA_FABRIL_ACCESS)
def get_eficiencia_fabril_dashboard(
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    op: str | None = Query(default=None),
    employee: str | None = Query(default=None),
    work_center: str | None = Query(default=None),
    status_ok_only: bool = Query(default=True),
    page: int = Query(default=1, ge=1),
    page_size: int | None = Query(default=None, ge=1, le=500),
):
    try:
        use_case = build_get_eficiencia_fabril_dashboard_use_case()
        result = use_case.execute(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            op=op,
            employee=employee,
            work_center=work_center,
            status_ok_only=status_ok_only,
            page=page,
            page_size=page_size,
        )

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_eficiencia_fabril_dashboard",
            message="Dashboard de eficiência fabril carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação no dashboard eficiência fabril: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar dashboard eficiência fabril: {exc}")
        return error_response(
            "Erro interno ao carregar dashboard de eficiência fabril.",
            status_code=500,
        )


@router.get("/eficiencia-fabril/appointments", **PRODUCTION_EFICIENCIA_FABRIL_APPOINTMENTS)
@require_any_permission(EFICIENCIA_FABRIL_ACCESS)
def get_eficiencia_fabril_appointments(
    date_start: str | None = Query(default=None),
    date_end: str | None = Query(default=None),
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    op: str | None = Query(default=None),
    employee: str | None = Query(default=None),
    work_center: str | None = Query(default=None),
    status_ok_only: bool = Query(default=False),
):
    try:
        use_case = build_get_eficiencia_fabril_appointments_use_case()
        result = use_case.execute(
            date_start=date_start,
            date_end=date_end,
            branch=branch,
            op=op,
            employee=employee,
            work_center=work_center,
            status_ok_only=status_ok_only,
        )

        return api_delpi_success(
            result,
            operation_id="list_eficiencia_fabril_appointments",
            message="Apontamentos de eficiência fabril carregados com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Erro de validação nos apontamentos eficiência fabril: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao carregar apontamentos eficiência fabril: {exc}")
        return error_response(
            "Erro interno ao carregar apontamentos de eficiência fabril.",
            status_code=500,
        )