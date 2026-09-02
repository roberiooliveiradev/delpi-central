from fastapi import APIRouter, Query
from typing import Optional

from app.core.responses import error_response
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error
from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_FINANCIAL_ACCESS

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.dto.financial.purchase_freight_links_request import (
    PurchaseFreightLinksRequest,
)
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.application.use_cases.financial.get_purchase_freight_links_use_case import (
    DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
)
from app.application.use_cases.financial.get_rol_invoices_use_case import (
    DEFAULT_ROL_INVOICE_LIMIT,
)
from app.composition.financial_composer import (
    build_get_purchase_freight_links_use_case,
    build_get_rol_use_case,
    build_get_rol_invoices_use_case,
    build_get_financial_ebitda_pct_use_case,
    build_get_financial_fixed_cost_pct_use_case,
    build_get_financial_pmr_use_case,
)
from app.interface.http.kpi_field_labels import (
    FINANCIAL_EBITDA_FIELD_LABELS,
    FINANCIAL_FIXED_COST_FIELD_LABELS,
    FINANCIAL_PMR_FIELD_LABELS,
    FINANCIAL_PURCHASE_FREIGHT_LINKS_FIELD_LABELS,
    FINANCIAL_ROL_FIELD_LABELS,
    FINANCIAL_ROL_INVOICES_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.openapi_agent_metadata import (
    FINANCIAL_EBITDA,
    FINANCIAL_FIXED_COST,
    FINANCIAL_PMR,
    FINANCIAL_ROL,
    FINANCIAL_ROL_INVOICES,
)
from app.interface.http.openapi_agent_metadata_builder import (
    OpenApiAgentMetadataBuilder,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
)


router = APIRouter(tags=["Financeiro"])


@router.get("/rol", **FINANCIAL_ROL)
@require_any_permission(KPI_FINANCIAL_ACCESS)
def get_rol(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        dto = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        use_case = build_get_rol_use_case()
        result = enrich_dashboard_metric(
            use_case.execute(dto),
            source_key=goal_keys.COMMERCIAL_ROL,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_financial_rol",
            message="ROL consultado com sucesso.",
            fields=kpi_fields(FINANCIAL_ROL_FIELD_LABELS),
        )

    except Exception as e:
        log_error(f"Erro ao consultar ROL: {e}")
        return error_response(str(e))


@router.get("/rol/invoices", **FINANCIAL_ROL_INVOICES)
@require_any_permission(KPI_FINANCIAL_ACCESS)
def get_rol_invoices(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    limit: int = Query(DEFAULT_ROL_INVOICE_LIMIT, ge=1, le=DEFAULT_ROL_INVOICE_LIMIT),
):
    try:
        dto = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )
        use_case = build_get_rol_invoices_use_case()
        result = use_case.execute(dto, limit=limit)
        return api_delpi_success(
            result,
            operation_id="get_financial_rol_invoices",
            message="Extrato de notas da ROL consultado com sucesso.",
            fields=kpi_fields(FINANCIAL_ROL_INVOICES_FIELD_LABELS),
        )
    except Exception as e:
        log_error(f"Erro ao consultar extrato de notas da ROL: {e}")
        return error_response(str(e))


@router.get(
    "/purchase-freight/links",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_financial_purchase_freight_links",
        path="/financial/purchase-freight/links",
    ),
)
@require_any_permission(KPI_FINANCIAL_ACCESS)
def get_financial_purchase_freight_links(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    issue_start: Optional[str] = Query(None),
    issue_end: Optional[str] = Query(None),
    entry_start: Optional[str] = Query(None),
    entry_end: Optional[str] = Query(None),
    supplier: Optional[str] = Query(None),
    invoice_document: Optional[str] = Query(None),
    freight_document: Optional[str] = Query(None),
    limit: int = Query(
        DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
        ge=1,
        le=DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
    ),
):
    try:
        dto = PurchaseFreightLinksRequest(
            branch=branch,
            issue_start=issue_start,
            issue_end=issue_end,
            entry_start=entry_start,
            entry_end=entry_end,
            supplier=supplier,
            invoice_document=invoice_document,
            freight_document=freight_document,
        )
        use_case = build_get_purchase_freight_links_use_case()
        result = use_case.execute(dto, limit=limit)
        return api_delpi_success(
            result,
            operation_id="get_financial_purchase_freight_links",
            message="Vínculos de frete de compra consultados com sucesso.",
            fields=kpi_fields(FINANCIAL_PURCHASE_FREIGHT_LINKS_FIELD_LABELS),
        )
    except Exception as e:
        log_error(f"Erro ao consultar vínculos de frete de compra: {e}")
        return error_response(str(e))


@router.get("/ebitda_pct", **FINANCIAL_EBITDA)
@require_any_permission(KPI_FINANCIAL_ACCESS)
def get_ebitda_pct(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        dto = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        use_case = build_get_financial_ebitda_pct_use_case()
        result = enrich_dashboard_metric(
            use_case.execute(dto),
            source_key=goal_keys.FINANCIAL_EBITDA,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_financial_ebitda_pct",
            message="EBITDA percentual buscado com sucesso.",
            fields=kpi_fields(FINANCIAL_EBITDA_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar EBITDA percentual: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar EBITDA percentual: {exc}")
        return error_response(
            "Erro interno ao buscar EBITDA percentual.",
            status_code=500,
        )


@router.get("/fixed_cost_pct", **FINANCIAL_FIXED_COST)
@require_any_permission(KPI_FINANCIAL_ACCESS)
def get_fixed_cost_pct(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        dto = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        use_case = build_get_financial_fixed_cost_pct_use_case()
        result = enrich_dashboard_metric(
            use_case.execute(dto),
            source_key=goal_keys.FINANCIAL_FIXED_COST,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_financial_fixed_cost_pct",
            message="Custos fixos percentuais buscados com sucesso.",
            fields=kpi_fields(FINANCIAL_FIXED_COST_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar custos fixos percentuais: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar custos fixos percentuais: {exc}")
        return error_response(
            "Erro interno ao buscar custos fixos percentuais.",
            status_code=500,
        )


@router.get("/pmr", **FINANCIAL_PMR)
@require_any_permission(KPI_FINANCIAL_ACCESS)
def get_pmr(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        dto = GetRolRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        use_case = build_get_financial_pmr_use_case()
        result = enrich_dashboard_metric(
            use_case.execute(dto),
            source_key=goal_keys.FINANCIAL_PMR,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_financial_pmr",
            message="Prazo médio de recebimento buscado com sucesso.",
            fields=kpi_fields(FINANCIAL_PMR_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Erro de validação ao buscar PMR: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Erro ao buscar PMR: {exc}")
        return error_response(
            "Erro interno ao buscar prazo médio de recebimento.",
            status_code=500,
        )