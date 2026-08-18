"""BFF analytics / OTD / OV — membership na commercial-api; TOTVS na api-delpi."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

from fastapi import APIRouter, Query, Request

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_ANALYTICS_PERMISSIONS,
    COMMERCIAL_MANAGE_PERMISSIONS,
    COMMERCIAL_PORTFOLIO_BILLING_SHARE_PERMISSIONS,
    COMMERCIAL_READ_PERMISSIONS,
    can_use_team_scope,
)
from commercial_app.application.use_cases.get_open_portfolio_summary import (
    GetOpenPortfolioSummaryUseCase,
)
from commercial_app.application.use_cases.get_open_portfolio_horizon import (
    GetOpenPortfolioHorizonUseCase,
)
from commercial_app.application.use_cases.get_portfolio_billing_share import (
    GetPortfolioBillingShareUseCase,
)
from commercial_app.application.use_cases.get_portfolio_billing_ranking import (
    GetPortfolioBillingRankingUseCase,
)
from commercial_app.core.auth_actor import current_user_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.composition.commercial_composer import build_delpi_commercial_gateway
from commercial_app.domain.services.opportunity_collaborator_summary_service import (
    OpportunityCollaboratorSummaryService,
)
from commercial_app.interface.http.routes.totvs_bff_helpers import (
    merge_totvs_params,
    resolve_analytics_portfolio_scope,
    unwrap_gateway_data,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics BFF"])


def _proxy(
    request: Request,
    *,
    operation_id: str,
    path: str,
    seller_id: str | None,
    portfolio_id: str | None,
    params: dict[str, Any],
    message: str,
    account_customer_code: str | None = None,
):
    try:
        scope = resolve_analytics_portfolio_scope(
            request, seller_id=seller_id, portfolio_id=portfolio_id
        )
        totvs_params = merge_totvs_params(
            scope,
            params,
            account_customer_code=account_customer_code,
        )
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            path, params=totvs_params
        )
        return ok(unwrap_gateway_data(payload), message=message, operation_id=operation_id)
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 400, operation_id=operation_id)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=operation_id)
    except Exception:
        logger.exception("%s_failed", operation_id)
        return fail("Erro interno no BFF analytics.", 500, operation_id=operation_id)


def _common_filters(
    *,
    start_date: str | None,
    end_date: str | None,
    branch: str | None,
    customer_segment: str | None,
    granularity: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    search: str | None = None,
    product_code: str | None = None,
    product_group: str | None = None,
) -> dict[str, Any]:
    return {
        "start_date": start_date,
        "end_date": end_date,
        "branch": branch,
        "customer_segment": customer_segment,
        "granularity": granularity,
        "status": status,
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
        "search": search,
        "product_code": product_code,
        "product_group": product_group,
    }


@router.get(
    "/portfolio-billing-share",
    operation_id="bff_get_analytics_portfolio_billing_share",
)
@require_any_permission(*COMMERCIAL_PORTFOLIO_BILLING_SHARE_PERMISSIONS)
def bff_portfolio_billing_share(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    """KPI-PORTFOLIO-SHARE: portfolioRol ÷ companyRol no período filtrado."""
    operation_id = "bff_get_analytics_portfolio_billing_share"
    try:
        scope = resolve_analytics_portfolio_scope(
            request, seller_id=seller_id, portfolio_id=portfolio_id
        )
        gateway = build_delpi_commercial_gateway()
        data = GetPortfolioBillingShareUseCase().execute(
            gateway,
            scope,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        )
        return ok(
            data,
            message="Share de faturamento da carteira carregado.",
            operation_id=operation_id,
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 400, operation_id=operation_id)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=operation_id)
    except Exception:
        logger.exception("%s_failed", operation_id)
        return fail("Erro interno no BFF analytics.", 500, operation_id=operation_id)


@router.get(
    "/portfolio-billing-ranking",
    operation_id="bff_get_analytics_portfolio_billing_ranking",
)
@require_any_permission(
    *COMMERCIAL_READ_PERMISSIONS,
    *COMMERCIAL_MANAGE_PERMISSIONS,
    *COMMERCIAL_ANALYTICS_PERMISSIONS,
    *COMMERCIAL_PORTFOLIO_BILLING_SHARE_PERMISSIONS,
)
def bff_portfolio_billing_ranking(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    group_by: str = Query(default="customer", pattern="^(customer|seller)$"),
    limit: int = Query(default=50, ge=1, le=500),
    order: str = Query(default="growth", pattern="^(growth|decline)$"),
):
    """Ranking delta % faturamento vs período −1 ano (cliente; vendedor se team/manage)."""
    operation_id = "bff_get_analytics_portfolio_billing_ranking"
    try:
        resolved_group = "seller" if group_by == "seller" else "customer"
        resolved_order = "decline" if order == "decline" else "growth"
        if resolved_group == "seller" and not can_use_team_scope(
            current_user_from_request(request)
        ):
            return fail(
                "Ranking por vendedor exige visão de equipe ou gestão de carteiras.",
                403,
                operation_id=operation_id,
            )
        if not start_date or not end_date:
            return fail(
                "start_date e end_date são obrigatórios.",
                400,
                operation_id=operation_id,
            )
        scope = resolve_analytics_portfolio_scope(
            request, seller_id=seller_id, portfolio_id=portfolio_id
        )
        gateway = build_delpi_commercial_gateway()
        data = GetPortfolioBillingRankingUseCase().execute(
            gateway,
            scope,
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            limit=limit,
            group_by=resolved_group,  # type: ignore[arg-type]
            order=resolved_order,  # type: ignore[arg-type]
        )
        return ok(
            data,
            message="Ranking de faturamento carregado.",
            operation_id=operation_id,
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 400, operation_id=operation_id)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=operation_id)
    except Exception:
        logger.exception("%s_failed", operation_id)
        return fail("Erro interno no BFF analytics.", 500, operation_id=operation_id)


@router.get(
    "/open-portfolio-summary",
    operation_id="bff_get_analytics_open_portfolio_summary",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_open_portfolio_summary(
    request: Request,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    """KPI-CARTEIRA: saldo em aberto agora (sem items; ignora período MTD/YTD)."""
    operation_id = "bff_get_analytics_open_portfolio_summary"
    try:
        scope = resolve_analytics_portfolio_scope(
            request, seller_id=seller_id, portfolio_id=portfolio_id
        )
        payload = build_delpi_commercial_gateway().list_open_orders()
        raw = unwrap_gateway_data(payload)
        data = GetOpenPortfolioSummaryUseCase().execute(
            raw if isinstance(raw, dict) else {},
            scope,
        )
        return ok(
            data,
            message="Resumo da carteira em aberto carregado.",
            operation_id=operation_id,
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 400, operation_id=operation_id)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=operation_id)
    except Exception:
        logger.exception("%s_failed", operation_id)
        return fail("Erro interno no BFF analytics.", 500, operation_id=operation_id)


@router.get(
    "/open-portfolio-horizon",
    operation_id="bff_get_analytics_open_portfolio_horizon",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_open_portfolio_horizon(
    request: Request,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    """KPI-CARTEIRA-HORIZON: buckets por data_entrega (snapshot; sem items)."""
    operation_id = "bff_get_analytics_open_portfolio_horizon"
    try:
        scope = resolve_analytics_portfolio_scope(
            request, seller_id=seller_id, portfolio_id=portfolio_id
        )
        payload = build_delpi_commercial_gateway().list_open_orders()
        raw = unwrap_gateway_data(payload)
        data = GetOpenPortfolioHorizonUseCase().execute(
            raw if isinstance(raw, dict) else {},
            scope,
        )
        return ok(
            data,
            message="Horizonte da carteira em aberto carregado.",
            operation_id=operation_id,
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id=operation_id)
    except LookupError as exc:
        return fail(str(exc), 404, operation_id=operation_id)
    except ValueError as exc:
        return fail(str(exc), 400, operation_id=operation_id)
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=operation_id)
    except Exception:
        logger.exception("%s_failed", operation_id)
        return fail("Erro interno no BFF analytics.", 500, operation_id=operation_id)


@router.get(
    "/head_office_rol_target_pct",
    operation_id="bff_get_head_office_rol_target_pct",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_head_office_rol(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_head_office_rol_target_pct",
        path="/head_office_rol_target_pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="ROL matriz carregado.",
    )


@router.get("/branch_rol_target_pct", operation_id="bff_get_branch_rol_target_pct")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_branch_rol(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_branch_rol_target_pct",
        path="/branch_rol_target_pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="ROL filial carregado.",
    )


@router.get(
    "/head_office_weg_rol_target_pct",
    operation_id="bff_get_head_office_weg_rol_target_pct",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_head_office_weg_rol(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_head_office_weg_rol_target_pct",
        path="/head_office_weg_rol_target_pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="ROL WEG matriz carregado.",
    )


@router.get(
    "/branch_weg_rol_target_pct",
    operation_id="bff_get_branch_weg_rol_target_pct",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_branch_weg_rol(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_branch_weg_rol_target_pct",
        path="/branch_weg_rol_target_pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="ROL WEG filial carregado.",
    )


@router.get(
    "/head_office_new_business_rol_target_pct",
    operation_id="bff_get_head_office_new_business_rol_target_pct",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_head_office_new_business_rol(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_head_office_new_business_rol_target_pct",
        path="/head_office_new_business_rol_target_pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="ROL novos negócios matriz carregado.",
    )


@router.get(
    "/branch_new_business_rol_target_pct",
    operation_id="bff_get_branch_new_business_rol_target_pct",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_branch_new_business_rol(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_branch_new_business_rol_target_pct",
        path="/branch_new_business_rol_target_pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="ROL novos negócios filial carregado.",
    )


@router.get("/department-idd", operation_id="bff_get_dashboard_department_idd")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_department_idd(
    request: Request,
    department_id: str = Query(default="commercial"),
    competence: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
):
    """IDD departamental (SI) — sem filtro de carteira; período/unidade no SI."""
    operation_id = "bff_get_dashboard_department_idd"
    try:
        params: dict[str, Any] = {"department_id": department_id}
        if competence:
            params["competence"] = competence
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        if branch:
            params["branch"] = branch
        payload = build_delpi_commercial_gateway().get_dashboard_department_idd(
            params=params
        )
        return ok(
            unwrap_gateway_data(payload),
            message="IDD departamental carregado.",
            operation_id=operation_id,
        )
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id=operation_id)
    except Exception:
        logger.exception("%s_failed", operation_id)
        return fail("Erro interno no BFF analytics.", 500, operation_id=operation_id)


@router.get("/closing-rate", operation_id="bff_get_closing_rate")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_closing_rate(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_closing_rate",
        path="/closing-rate",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="Taxa de conversão carregada.",
    )


@router.get("/closing-rate/series", operation_id="bff_get_sales_conversion_rate_series")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_closing_rate_series(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_segment: str | None = None,
    granularity: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_sales_conversion_rate_series",
        path="/closing-rate/series",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=None,
            customer_segment=customer_segment,
            granularity=granularity,
        ),
        message="Série da taxa de conversão carregada.",
    )


@router.get("/sales-order-otd", operation_id="bff_get_sales_order_otd")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_sales_order_otd(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_sales_order_otd",
        path="/sales-order-otd",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="OTD carregado.",
    )


@router.get("/new-business-rol-pct", operation_id="bff_get_new_business_rol_pct")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_new_business(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_new_business_rol_pct",
        path="/new-business-rol-pct",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
        ),
        message="Novos negócios carregados.",
    )


@router.get("/rol/series", operation_id="bff_get_commercial_rol_series")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_rol_series(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    granularity: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_commercial_rol_series",
        path="/rol/series",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            granularity=granularity,
        ),
        message="Série ROL carregada.",
    )


@router.get("/proposals", operation_id="bff_list_commercial_proposals")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_list_proposals(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    search: str | None = None,
    product_code: str | None = Query(default=None),
    product_group: str | None = Query(default=None),
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
    account_customer_code: str | None = Query(
        default=None,
        description="Conta 360: filtra OVs deste código sem membership de carteira.",
    ),
):
    return _proxy(
        request,
        operation_id="bff_list_commercial_proposals",
        path="/proposals",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        account_customer_code=account_customer_code,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
            product_code=product_code,
            product_group=product_group,
        ),
        message="Oportunidades carregadas.",
    )


@router.get(
    "/opportunity-collaborator-summary",
    operation_id="bff_opportunity_collaborator_summary",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_opportunity_collaborator_summary(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    status: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    """Aggregate OV counts by seller from the scoped proposals list (page cap 200)."""
    try:
        scope = resolve_analytics_portfolio_scope(
            request, seller_id=seller_id, portfolio_id=portfolio_id
        )
        totvs_params = merge_totvs_params(
            scope,
            _common_filters(
                start_date=start_date,
                end_date=end_date,
                branch=branch,
                customer_segment=customer_segment,
                status=status,
                page=1,
                page_size=200,
            ),
        )
        payload = build_delpi_commercial_gateway().get_commercial_analytics(
            "/proposals", params=totvs_params
        )
        data = unwrap_gateway_data(payload)
        items = []
        truncated = False
        total = 0
        if isinstance(data, dict):
            raw_items = data.get("items")
            items = [item for item in raw_items if isinstance(item, dict)] if isinstance(raw_items, list) else []
            total = int(data.get("total") or len(items))
            truncated = total > len(items)
        rows = OpportunityCollaboratorSummaryService().summarize(items)
        return ok(
            {"items": rows, "sourceCount": len(items), "total": total, "truncated": truncated},
            message="Resumo de oportunidades por colaborador.",
            operation_id="bff_opportunity_collaborator_summary",
        )
    except PermissionError as exc:
        return fail(str(exc), 403, operation_id="bff_opportunity_collaborator_summary")
    except LookupError as exc:
        return fail(str(exc), 404, operation_id="bff_opportunity_collaborator_summary")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="bff_opportunity_collaborator_summary")
    except RuntimeError as exc:
        return fail(str(exc), 502, operation_id="bff_opportunity_collaborator_summary")
    except Exception:
        logger.exception("bff_opportunity_collaborator_summary_failed")
        return fail(
            "Erro ao agregar oportunidades por colaborador.",
            500,
            operation_id="bff_opportunity_collaborator_summary",
        )


@router.get(
    "/proposals/{proposal_number}",
    operation_id="bff_get_commercial_proposal",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_get_proposal(
    request: Request,
    proposal_number: str,
    branch: str = Query(...),
    revision: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    encoded = quote(proposal_number.strip(), safe="")
    return _proxy(
        request,
        operation_id="bff_get_commercial_proposal",
        path=f"/proposals/{encoded}",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params={"branch": branch, "revision": revision},
        message="Detalhe da OV carregado.",
    )


@router.get(
    "/proposals/{proposal_number}/history/events",
    operation_id="bff_get_commercial_proposal_history_events",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_proposal_history(
    request: Request,
    proposal_number: str,
    branch: str = Query(...),
    revision: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    encoded = quote(proposal_number.strip(), safe="")
    return _proxy(
        request,
        operation_id="bff_get_commercial_proposal_history_events",
        path=f"/proposals/{encoded}/history/events",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params={
            "branch": branch,
            "revision": revision,
            "start_date": start_date,
            "end_date": end_date,
        },
        message="Histórico da OV carregado.",
    )


@router.get("/sales-order-otd/panel", operation_id="bff_get_sales_order_otd_panel")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_otd_panel(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    status: str | None = None,
    page: int | None = None,
    page_size: int | None = None,
    sort_by: str | None = None,
    sort_dir: str | None = None,
    search: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_sales_order_otd_panel",
        path="/sales-order-otd/panel",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            status=status,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_dir=sort_dir,
            search=search,
        ),
        message="Painel OTD carregado.",
    )


@router.get("/sales-order-otd/series", operation_id="bff_get_sales_order_otd_series")
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_otd_series(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    branch: str | None = None,
    customer_segment: str | None = None,
    granularity: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    return _proxy(
        request,
        operation_id="bff_get_sales_order_otd_series",
        path="/sales-order-otd/series",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=branch,
            customer_segment=customer_segment,
            granularity=granularity,
        ),
        message="Série OTD carregada.",
    )


@router.get(
    "/sales-order-otd/lines/{branch}/{order_number}/{line_item}",
    operation_id="bff_get_sales_order_otd_line_detail",
)
@require_any_permission(*COMMERCIAL_ANALYTICS_PERMISSIONS)
def bff_otd_line(
    request: Request,
    branch: str,
    order_number: str,
    line_item: str,
    start_date: str | None = None,
    end_date: str | None = None,
    customer_segment: str | None = None,
    seller_id: str | None = Query(default=None),
    portfolio_id: str | None = Query(default=None),
):
    b = quote(branch.strip(), safe="")
    o = quote(order_number.strip(), safe="")
    line = quote(line_item.strip(), safe="")
    return _proxy(
        request,
        operation_id="bff_get_sales_order_otd_line_detail",
        path=f"/sales-order-otd/lines/{b}/{o}/{line}",
        seller_id=seller_id,
        portfolio_id=portfolio_id,
        params=_common_filters(
            start_date=start_date,
            end_date=end_date,
            branch=None,
            customer_segment=customer_segment,
        ),
        message="Detalhe da linha OTD carregado.",
    )
