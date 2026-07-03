from fastapi import APIRouter, Query
from typing import Optional

from delpi_auth.authorization import require_any_permission

from app.application.security.api_delpi_permissions import KPI_COMMERCIAL_ACCESS
from app.core.responses import error_response, not_found_response
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
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
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
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
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
    granularity: str = Query(..., min_length=3, max_length=10),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
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
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    status: Optional[str] = Query(
        None,
        description="Filtro: won (ganhas), open (demais) ou omitir para todas.",
    ),
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: Optional[str] = Query(
        None,
        description=(
            "Coluna de ordenação: branch, proposal_number, revision, description, "
            "proposal_date, end_date, status_code, customer_code, customer_store."
        ),
    ),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
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
    branch: str = Query(..., min_length=2, max_length=2),
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
    branch: str = Query(..., min_length=2, max_length=2),
    revision: Optional[str] = Query(None, min_length=1, max_length=2),
    date_start: Optional[str] = Query(None),
    date_end: Optional[str] = Query(None),
):
    try:
        dto = build_get_lmp_history_request(
            proposal_number,
            date_start=date_start,
            date_end=date_end,
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
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
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
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
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
    "/sales-order-otd",
    **OpenApiAgentMetadataBuilder.from_contract(
        "get_sales_order_otd",
        path="/commercial/sales-order-otd",
    ),
)
@require_any_permission(KPI_COMMERCIAL_ACCESS)
def get_sales_order_otd(
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
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
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    customer_segment: Optional[str] = Query(
        None,
        description="Segmento de cliente: weg ou new_business.",
    ),
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
    branch: Optional[str] = Query(None, min_length=2, max_length=2),
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
