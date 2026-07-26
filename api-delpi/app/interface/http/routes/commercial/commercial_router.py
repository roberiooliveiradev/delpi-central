from fastapi import APIRouter, Query

from app.interface.http.query_param_enums import (
    BRANCH_QUERY_OPTIONAL,
    BRANCH_QUERY_REQUIRED,
    COMMERCIAL_OTD_STATUS_QUERY,
    COMMERCIAL_PROPOSAL_STATUS_QUERY,
    CUSTOMER_SEGMENT_QUERY,
    GRANULARITY_QUERY_REQUIRED,
    SORT_DIR_QUERY,
)
from typing import Optional

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_COMMERCIAL_ACCESS
from app.core.responses import error_response, not_found_response
from app.interface.http.period_query_params import (
    END_DATE_QUERY,
    LEGACY_DATE_END_QUERY,
    LEGACY_DATE_START_QUERY,
    START_DATE_QUERY,
    resolve_period_dates,
)
from app.interface.http.route_response_helpers import api_delpi_success
from app.utils.logger import log_error

from app.application.dto.commercial.commercial_target_request import CommercialTargetRequest
from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.dto.commercial.sales_conversion_rate_request import SalesConversionRateRequest
from app.application.dto.commercial.new_clients_average_request import NewClientsAverageRequest
from app.application.dto.commercial.new_clients_rol_pct_request import NewClientsRolPctRequest
from app.application.dto.commercial.commercial_rol_series_request import (
    CommercialRolSeriesRequest,
)
from app.application.dto.commercial.new_business_rol_pct_request import NewBusinessRolPctRequest
from app.application.dto.commercial.sales_order_otd_request import SalesOrderOtdRequest
from app.application.dto.commercial.get_sales_order_otd_panel_request import (
    GetSalesOrderOtdPanelRequest,
)
from app.application.dto.commercial.sales_order_otd_series_request import (
    SalesOrderOtdSeriesRequest,
)
from app.application.dto.commercial.get_sales_order_otd_line_detail_request import (
    GetSalesOrderOtdLineDetailRequest,
)
from app.application.services.strategic_indicators import dashboard_goal_source_keys as goal_keys
from app.composition.commercial_composer import (
    build_get_head_office_rol_target_pct_use_case,
    build_get_branch_rol_target_pct_use_case,
    build_get_sales_conversion_rate_use_case,
    build_list_commercial_proposals_use_case,
    build_get_commercial_proposal_use_case,
    build_get_new_clients_average_use_case,
    build_get_new_clients_rol_pct_use_case,
    build_get_commercial_rol_series_use_case,
    build_get_sales_order_otd_use_case,
    build_get_sales_order_otd_panel_use_case,
    build_get_sales_order_otd_series_use_case,
    build_get_sales_order_otd_line_detail_use_case,
    build_get_new_business_rol_pct_use_case,
    build_get_head_office_weg_rol_target_use_case,
    build_get_branch_weg_rol_target_use_case,
    build_get_head_office_new_business_rol_target_use_case,
    build_get_branch_new_business_rol_target_use_case,
)
from app.composition.engineering_composer import (
    build_engineering_get_lmp_history_events_use_case,
)
from app.interface.http.routes.commercial.commercial_route_helpers import (
    build_get_commercial_proposal_request,
    parse_customer_segment,
)
from app.interface.http.routes.engineering.lmp_route_helpers import (
    build_get_lmp_history_request,
)
from app.interface.http.kpi_field_labels import (
    COMMERCIAL_CONVERSION_FIELD_LABELS,
    COMMERCIAL_ROL_FIELD_LABELS,
    COMMERCIAL_SALES_ORDER_OTD_FIELD_LABELS,
    kpi_fields,
)
from app.interface.http.routes.shared.dashboard_goal_enrichment import enrich_dashboard_metric
from app.interface.http.openapi_agent_metadata import (
    COMMERCIAL_PROPOSAL_DETAIL,
    COMMERCIAL_PROPOSAL_HISTORY_EVENTS,
    COMMERCIAL_PROPOSALS,
)
from app.interface.http.openapi_agent_metadata_builder import OpenApiAgentMetadataBuilder


router = APIRouter(prefix="/commercial", tags=["Comercial"])


@router.get(
    "/head_office_rol_target_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_head_office_rol_target_pct",
        path="/commercial/head_office_rol_target_pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_head_office_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        use_case = build_get_head_office_rol_target_pct_use_case()

        request = CommercialTargetRequest(
            branch="01",
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_ROL,
            start_date=start_date,
            end_date=end_date,
            branch="01",
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_head_office_rol_target_pct",
            message="Head office ROL target percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching head office ROL target percentage: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching head office ROL target percentage: {exc}")
        return error_response(
            "Internal error while fetching head office ROL target percentage.",
            status_code=500,
        )


@router.get(
    "/branch_rol_target_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_branch_rol_target_pct",
        path="/commercial/branch_rol_target_pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_branch_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        use_case = build_get_branch_rol_target_pct_use_case()

        request = CommercialTargetRequest(
            branch="02",
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_ROL,
            start_date=start_date,
            end_date=end_date,
            branch="02",
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_branch_rol_target_pct",
            message="Branch ROL target percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching branch ROL target percentage: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching branch ROL target percentage: {exc}")
        return error_response(
            "Internal error while fetching branch ROL target percentage.",
            status_code=500,
        )


@router.get(
    "/head_office_weg_rol_target_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_head_office_weg_rol_target_pct",
        path="/commercial/head_office_weg_rol_target_pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_head_office_weg_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_head_office_weg_rol_target_use_case()

        request = CommercialTargetRequest(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_ROL_WEG,
            start_date=start_date,
            end_date=end_date,
            branch="01",
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_head_office_weg_rol_target_pct",
            message="Head office WEG ROL target percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching head office WEG ROL target: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching head office WEG ROL target: {exc}")
        return error_response(
            "Internal error while fetching head office WEG ROL target.",
            status_code=500,
        )


@router.get(
    "/branch_weg_rol_target_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_branch_weg_rol_target_pct",
        path="/commercial/branch_weg_rol_target_pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_branch_weg_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_branch_weg_rol_target_use_case()

        request = CommercialTargetRequest(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_ROL_WEG,
            start_date=start_date,
            end_date=end_date,
            branch="02",
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_branch_weg_rol_target_pct",
            message="Branch WEG ROL target percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching branch WEG ROL target: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching branch WEG ROL target: {exc}")
        return error_response(
            "Internal error while fetching branch WEG ROL target.",
            status_code=500,
        )


@router.get(
    "/head_office_new_business_rol_target_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_head_office_new_business_rol_target_pct",
        path="/commercial/head_office_new_business_rol_target_pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_head_office_new_business_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_head_office_new_business_rol_target_use_case()

        request = CommercialTargetRequest(
            branch="01",
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_ROL_NEW_BUSINESS,
            start_date=start_date,
            end_date=end_date,
            branch="01",
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_head_office_new_business_rol_target_pct",
            message="Head office new business ROL target percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(
            f"Validation error while fetching head office new business ROL target: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching head office new business ROL target: {exc}")
        return error_response(
            "Internal error while fetching head office new business ROL target.",
            status_code=500,
        )


@router.get(
    "/branch_new_business_rol_target_pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_branch_new_business_rol_target_pct",
        path="/commercial/branch_new_business_rol_target_pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_branch_new_business_rol_target_pct(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_branch_new_business_rol_target_use_case()

        request = CommercialTargetRequest(
            branch="02",
            start_date=start_date,
            end_date=end_date,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_ROL_NEW_BUSINESS,
            start_date=start_date,
            end_date=end_date,
            branch="02",
            recompute_target_pct_from="rol",
        )

        return api_delpi_success(
            result,
            operation_id="get_branch_new_business_rol_target_pct",
            message="Branch new business ROL target percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching branch new business ROL target: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching branch new business ROL target: {exc}")
        return error_response(
            "Internal error while fetching branch new business ROL target.",
            status_code=500,
        )


@router.get(
    "/rol/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_commercial_rol_series",
        path="/commercial/rol/series",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_commercial_rol_series(
    granularity: str = GRANULARITY_QUERY_REQUIRED(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        request = CommercialRolSeriesRequest(
            granularity=granularity,
            date_start=start_date,
            date_end=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        request.validate()

        use_case = build_get_commercial_rol_series_use_case()
        result = use_case.execute(request)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_commercial_rol_series",
            message="Commercial ROL series fetched successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching commercial ROL series: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching commercial ROL series: {exc}")
        return error_response(
            "Internal error while fetching commercial ROL series.",
            status_code=500,
        )


@router.get("/proposals", **COMMERCIAL_PROPOSALS)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def list_commercial_proposals(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = COMMERCIAL_PROPOSAL_STATUS_QUERY(),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: Optional[str] = Query(
        None,
        description=(
            "Coluna de ordenação: branch, proposal_number, revision, description, "
            "proposal_date, end_date, status_code, customer_code, customer_store."
        ),
    ),
    sort_dir: str = SORT_DIR_QUERY(),
    search: Optional[str] = Query(
        None,
        max_length=80,
        description=(
            "Busca textual em filial, número da proposta, revisão, descrição, "
            "status, cliente, loja e estágio."
        ),
    ),
):
    try:
        use_case = build_list_commercial_proposals_use_case()

        request = ListCommercialProposalsRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            status=status,
            customer_segment=parse_customer_segment(customer_segment),
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        )

        result = use_case.execute(request)

        return api_delpi_success(
            result,
            operation_id="list_commercial_proposals",
            message="Commercial proposals listed successfully.",
        )

    except ValueError as exc:
        log_error(f"Validation error while listing commercial proposals: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while listing commercial proposals: {exc}")
        return error_response(
            "Internal error while listing commercial proposals.",
            status_code=500,
        )


@router.get("/proposals/{proposal_number}", **COMMERCIAL_PROPOSAL_DETAIL)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_commercial_proposal(
    proposal_number: str,
    branch: str = BRANCH_QUERY_REQUIRED(),
    revision: Optional[str] = Query(None, min_length=1, max_length=2),
):
    try:
        request = build_get_commercial_proposal_request(
            proposal_number,
            branch=branch,
            revision=revision,
        )
        use_case = build_get_commercial_proposal_use_case()
        result = use_case.execute(request)

        return api_delpi_success(
            result,
            operation_id="get_commercial_proposal",
            message="Commercial proposal loaded successfully.",
        )

    except ValueError as exc:
        message = str(exc)
        if "não encontrada" in message.lower():
            return not_found_response(message)
        log_error(f"Validation error while loading commercial proposal: {exc}")
        return error_response(message, status_code=400)

    except Exception as exc:
        log_error(f"Error while loading commercial proposal: {exc}")
        return error_response(
            "Internal error while loading commercial proposal.",
            status_code=500,
        )


@router.get(
    "/proposals/{proposal_number}/history/events",
    **COMMERCIAL_PROPOSAL_HISTORY_EVENTS,
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_commercial_proposal_history_events(
    proposal_number: str,
    branch: str = BRANCH_QUERY_REQUIRED(),
    revision: Optional[str] = Query(None, min_length=1, max_length=2),
    start_date: Optional[str] = START_DATE_QUERY(),
    end_date: Optional[str] = END_DATE_QUERY(),
    date_start: Optional[str] = LEGACY_DATE_START_QUERY(),
    date_end: Optional[str] = LEGACY_DATE_END_QUERY(),
):
    start_date, end_date = resolve_period_dates(
        start_date=start_date,
        end_date=end_date,
        date_start=date_start,
        date_end=date_end,
    )
    try:
        dto = build_get_lmp_history_request(
            proposal_number,
            date_start=start_date,
            date_end=end_date,
            branch=branch,
            revision=revision,
        )
        use_case = build_engineering_get_lmp_history_events_use_case()
        result = use_case.execute(dto)

        return api_delpi_success(
            result,
            operation_id="get_commercial_proposal_history_events",
            message="Commercial proposal history events loaded successfully.",
        )

    except ValueError as exc:
        log_error(
            f"Validation error while loading commercial proposal history: {exc}"
        )
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while loading commercial proposal history: {exc}")
        return error_response(
            "Internal error while loading commercial proposal history.",
            status_code=500,
        )


@router.get(
    "/closing-rate",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_sales_conversion_rate",
        path="/commercial/closing-rate",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_sales_conversion_rate(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        use_case = build_get_sales_conversion_rate_use_case()

        request = SalesConversionRateRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_SALES_CONVERSION,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_sales_conversion_rate",
            message="Sales Conversion Rate fetched successfully.",
            fields=kpi_fields(COMMERCIAL_CONVERSION_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching Sales Conversion Rate: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching Sales Conversion Rate: {exc}")
        return error_response(
            "Internal error while fetching Sales Conversion Rate.",
            status_code=500,
        )
    

@router.get(
    "/new-clients-average",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_new_clients_average",
        path="/commercial/new-clients-average",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_new_clients_average(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_new_clients_average_use_case()

        request = NewClientsAverageRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return api_delpi_success(
            result,
            operation_id="get_new_clients_average",
            message="Number of New Clients (Monthly Average) fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching Number of New Clients (Monthly Average): {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching Number of New Clients (Monthly Average): {exc}")
        return error_response(
            "Internal error while fetching Number of New Clients (Monthly Average).",
            status_code=500,
        )
    

@router.get(
    "/sales-order-otd/series",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_sales_order_otd_series",
        path="/commercial/sales-order-otd/series",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_sales_order_otd_series(
    granularity: str = GRANULARITY_QUERY_REQUIRED(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        request = SalesOrderOtdSeriesRequest(
            granularity=granularity,
            date_start=start_date,
            date_end=end_date,
            branch=branch,
            customer_segment=parse_customer_segment(customer_segment),
        )

        use_case = build_get_sales_order_otd_series_use_case()
        result = use_case.execute(request)

        return api_delpi_success(
            result.to_dict(),
            operation_id="get_sales_order_otd_series",
            message="Série temporal de OTD de pedidos de venda carregada com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching sales order OTD series: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching sales order OTD series: {exc}")
        return error_response(
            "Internal error while fetching sales order OTD series.",
            status_code=500,
        )


@router.get(
    "/sales-order-otd/panel",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_sales_order_otd_panel",
        path="/commercial/sales-order-otd/panel",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_sales_order_otd_panel(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
    status: Optional[str] = COMMERCIAL_OTD_STATUS_QUERY(),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=1000),
    sort_by: Optional[str] = Query(default=None),
    sort_dir: str = SORT_DIR_QUERY(),
):
    try:
        use_case = build_get_sales_order_otd_panel_use_case()

        request = GetSalesOrderOtdPanelRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_SALES_ORDER_OTD,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            summary_key="summary",
        )

        return api_delpi_success(
            result,
            operation_id="get_sales_order_otd_panel",
            message="Painel de OTD de pedidos de venda carregado com sucesso.",
            fields=kpi_fields(COMMERCIAL_SALES_ORDER_OTD_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching sales order OTD panel: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching sales order OTD panel: {exc}")
        return error_response(
            "Internal error while fetching sales order OTD panel.",
            status_code=500,
        )


@router.get(
    "/sales-order-otd/lines/{branch}/{order_number}/{line_item}",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_sales_order_otd_line_detail",
        path="/commercial/sales-order-otd/lines/{branch}/{order_number}/{line_item}",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_sales_order_otd_line_detail(
    branch: str,
    order_number: str,
    line_item: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        use_case = build_get_sales_order_otd_line_detail_use_case()

        request = GetSalesOrderOtdLineDetailRequest(
            branch=branch.strip(),
            order_number=order_number.strip(),
            line_item=line_item.strip(),
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        result = use_case.execute(request)

        return api_delpi_success(
            result,
            operation_id="get_sales_order_otd_line_detail",
            message="Detalhe da linha de pedido de venda carregado com sucesso.",
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching sales order OTD line: {exc}")
        if "não encontrada" in str(exc).lower():
            return not_found_response(str(exc))
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching sales order OTD line: {exc}")
        return error_response(
            "Internal error while fetching sales order OTD line detail.",
            status_code=500,
        )


@router.get(
    "/sales-order-otd",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_sales_order_otd",
        path="/commercial/sales-order-otd",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_sales_order_otd(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        use_case = build_get_sales_order_otd_use_case()

        request = SalesOrderOtdRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_SALES_ORDER_OTD,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_sales_order_otd",
            message="Sales order on-time delivery percentage fetched successfully.",
            fields=kpi_fields(COMMERCIAL_SALES_ORDER_OTD_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching sales order OTD: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching sales order OTD: {exc}")
        return error_response(
            "Internal error while fetching sales order OTD.",
            status_code=500,
        )


@router.get(
    "/new-business-rol-pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_new_business_rol_pct",
        path="/commercial/new-business-rol-pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_new_business_rol_pct(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = CUSTOMER_SEGMENT_QUERY(),
):
    try:
        use_case = build_get_new_business_rol_pct_use_case()

        request = NewBusinessRolPctRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
            customer_segment=parse_customer_segment(customer_segment),
        )

        result = enrich_dashboard_metric(
            use_case.execute(request),
            source_key=goal_keys.COMMERCIAL_NEW_BUSINESS_ROL,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
        )

        return api_delpi_success(
            result,
            operation_id="get_new_business_rol_pct",
            message="New business share of net operating revenue fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching new business ROL %: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching new business ROL %: {exc}")
        return error_response(
            "Internal error while fetching new business ROL %.",
            status_code=500,
        )


@router.get(
    "/new-clients-rol-pct",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_new_clients_rol_pct",
        path="/commercial/new-clients-rol-pct",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_new_clients_rol_pct(
    branch: Optional[str] = BRANCH_QUERY_OPTIONAL(),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    try:
        use_case = build_get_new_clients_rol_pct_use_case()

        request = NewClientsRolPctRequest(
            branch=branch,
            start_date=start_date,
            end_date=end_date,
        )

        result = use_case.execute(request)

        return api_delpi_success(
            result,
            operation_id="get_new_clients_rol_pct",
            message="% of Net Operating Revenue from New Clients fetched successfully.",
            fields=kpi_fields(COMMERCIAL_ROL_FIELD_LABELS),
        )

    except ValueError as exc:
        log_error(f"Validation error while fetching % of Net Operating Revenue from New Clients: {exc}")
        return error_response(str(exc), status_code=400)

    except Exception as exc:
        log_error(f"Error while fetching % of Net Operating Revenue from New Clients: {exc}")
        return error_response(
            "Internal error while fetching % of Net Operating Revenue from New Clients.",
            status_code=500,
        )
