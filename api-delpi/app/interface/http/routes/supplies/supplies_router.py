from fastapi import APIRouter, Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    STOCK_METHOD_QUERY,
)

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_SUPPLIES_ACCESS
from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

from app.application.dto.supplies.get_cpv_request import GetCPVRequest
from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.application.dto.supplies.get_stock_value_request import GetStockValueRequest
from app.application.dto.supplies.get_inventory_turnover_request import (
    GetInventoryTurnoverRequest,
)
from app.application.dto.supplies.negotiation_savings_summary_request import (
    NegotiationSavingsSummaryRequest,
)
from app.application.services.strategic_indicators.dashboard_goal_dates import (
    normalize_si_branch,
)

from app.interface.http.openapi_agent_metadata import (
    SUPPLIES_CPV,
    SUPPLIES_INVENTORY_TURNOVER,
    SUPPLIES_NEGOTIATION_SAVINGS,
    SUPPLIES_OTD,
    SUPPLIES_STOCK_VALUE,
)
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.supplies_composer import (
    build_get_cpv_use_case,
    build_get_negotiation_savings_summary_use_case,
    build_get_otd_use_case,
    build_get_stock_value_use_case,
    build_get_inventory_turnover_use_case,
)
from app.interface.http.kpi_field_labels import (
    SUPPLIES_CPV_FIELD_LABELS,
    SUPPLIES_INVENTORY_TURNOVER_FIELD_LABELS,
    SUPPLIES_NEGOTIATION_SAVINGS_FIELD_LABELS,
    SUPPLIES_OTD_FIELD_LABELS,
    SUPPLIES_STOCK_VALUE_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric

router = APIRouter(prefix="/supplies", tags=["Suprimentos"])


@router.get("/cpv", **SUPPLIES_CPV)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_cpv(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    top_limit: int = Query(default=5, ge=1, le=20),
):
    try:
        use_case = build_get_cpv_use_case()

        request = GetCPVRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            top_limit=top_limit,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.SUPPLIES_CPV,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_supplies_cpv",
            message="CPV buscado com sucesso.",
            fields=kpi_fields(SUPPLIES_CPV_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar CPV: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar CPV: {exc}")
        return error_response(
            "Erro interno ao buscar CPV.",
            status_code=500,
        )
    

@router.get("/otd", **SUPPLIES_OTD)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_otd(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    top_limit: int = Query(default=5, ge=1, le=20),
    details_limit: int = Query(default=20, ge=1, le=100),
):
    try:
        use_case = build_get_otd_use_case()

        request = GetOTDRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            top_limit=top_limit,
            details_limit=details_limit,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.SUPPLIES_OTD,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_supplies_otd",
            message="OTD buscado com sucesso.",
            fields=kpi_fields(SUPPLIES_OTD_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar OTD: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar OTD: {exc}")
        return error_response(
            "Erro interno ao buscar OTD.",
            status_code=500,
        )
    

@router.get("/stock-value", **SUPPLIES_STOCK_VALUE)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_stock_value(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    location: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    top_limit: int = Query(default=10, ge=1, le=50),
    summary_only: bool = Query(
        default=False,
        description="Quando true, retorna apenas o resumo consolidado (sem breakdown por filial/local/produto).",
    ),
    stock_method: str = STOCK_METHOD_QUERY,
):
    try:
        use_case = build_get_stock_value_use_case()

        request = GetStockValueRequest(
            branch=branch,
            location=location,
            start_date=start_date,
            end_date=end_date,
            top_limit=top_limit,
            summary_only=summary_only,
            stock_method=stock_method,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.SUPPLIES_STOCK_VALUE,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_supplies_stock_value",
            message="Valor total de estoque buscado com sucesso.",
            fields=kpi_fields(SUPPLIES_STOCK_VALUE_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar valor total de estoque: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar valor total de estoque: {exc}")
        return error_response(
            "Erro interno ao buscar valor total de estoque.",
            status_code=500,
        )
    

@router.get("/negotiation-savings/summary", **SUPPLIES_NEGOTIATION_SAVINGS)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_negotiation_savings_summary(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
):
    try:
        use_case = build_get_negotiation_savings_summary_use_case()

        request = NegotiationSavingsSummaryRequest(
            branch=normalize_si_branch(branch),
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request).to_dict(),
            source_key=goal_keys.SUPPLIES_NEGOTIATION_SAVINGS,
            start_date=start_date,
            end_date=end_date,
            branch=normalize_si_branch(branch),
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_supplies_negotiation_savings_summary",
            message="Economia em negociações de compras buscada com sucesso.",
            fields=kpi_fields(SUPPLIES_NEGOTIATION_SAVINGS_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(
            f"Erro de validação ao buscar economia em negociações de compras: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar economia em negociações de compras: {exc}")
        return error_response(
            "Erro interno ao buscar economia em negociações de compras.",
            status_code=500,
        )


@router.get("/inventory-turnover", **SUPPLIES_INVENTORY_TURNOVER)
@require_any_permission(KPI_SUPPLIES_ACCESS)
def get_inventory_turnover(
    branch: str | None = BRANCH_QUERY_OPTIONAL,
    location: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    strict_idd_period: bool = Query(default=False),
):
    try:
        use_case = build_get_inventory_turnover_use_case()

        request = GetInventoryTurnoverRequest(
            branch=branch,
            location=location,
            start_date=start_date,
            end_date=end_date,
            strict_idd_period=strict_idd_period,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.SUPPLIES_STOCK_TURNOVER,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        stock_context = result.get("stock_context")
        if isinstance(stock_context, dict):
            result["stock_context"] = enrich_dashboard_metric(
                stock_context,
                source_key=goal_keys.SUPPLIES_STOCK_VALUE,
                start_date=start_date,
                end_date=end_date,
                branch=branch,
            )

        return api_delpi_success(
            result,
            operation_id="get_supplies_inventory_turnover",
            message="Giro de estoque buscado com sucesso.",
            fields=kpi_fields(SUPPLIES_INVENTORY_TURNOVER_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar giro de estoque: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar giro de estoque: {exc}")
        return error_response(
            "Erro interno ao buscar giro de estoque.",
            status_code=500,
        )