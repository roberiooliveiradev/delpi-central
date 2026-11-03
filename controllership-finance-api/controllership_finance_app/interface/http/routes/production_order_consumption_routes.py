"""R04 governed production-order consumption view — visão operacional.

BFF owns: human principal + ``controllership-finance.access`` (Core
effective permissions), delegation of the user Bearer, officiality
projection and typed error passthrough. All Protheus data comes from
the api-delpi ``consumption-audit`` producer (reuso aprovado G059) —
nothing here recomputes consumption, and unavailable fields stay typed
absence upstream. MATR860 equivalence is NOT claimed.
"""

from __future__ import annotations

import calendar
from typing import Any

from fastapi import APIRouter, Path, Query, Request

from controllership_finance_app.core.responses import ok
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    ApiDelpiSettlementsGateway,
    DelpiApiGatewayError,
)
from controllership_finance_app.interface.http.routes.closing_routes import (
    _authorized_user,
    _map_gateway_error,
    _user_bearer,
)

router = APIRouter(prefix="/closing", tags=["Production Order Consumption"])

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"

_LIMITATIONS = [
    "Visão operacional — equivalência com o relatório oficial MATR860 "
    "não homologada (officialParity=pending).",
    "O filtro temporal atua sobre a data da OP escolhida por date_type "
    "(emission|finished|appointment), não sobre a data do movimento de "
    "consumo — OPs que atravessam competências seguem a semântica do "
    "produtor.",
    "Centro de trabalho não é projetado na listagem — informado por "
    "operação (SH8) e disponível no detalhe da OP; uma ordem pode "
    "envolver vários centros.",
]


def _period_bounds(period: str) -> tuple[str, str]:
    year, month = int(period[:4]), int(period[5:7])
    last_day = calendar.monthrange(year, month)[1]
    return f"{year:04d}-{month:02d}-01", f"{year:04d}-{month:02d}-{last_day:02d}"


def _projection(
    data: dict[str, Any], *, period: str, branch: str, date_type: str
) -> dict[str, Any]:
    """Envelope projection — keeps producer payload untouched, adds
    governed metadata."""
    out = dict(data)
    out["period"] = period
    out["branch"] = branch
    out["dateType"] = date_type
    out["officiality"] = "operational_view"
    out["officialParity"] = "pending"
    out["provenance"] = (
        "api-delpi consumption-audit (SC2/SG1/SD4/SD3 — read-only)"
    )
    out["limitations"] = _LIMITATIONS
    return out


@router.get(
    "/competences/{period}/production-order-consumption",
    operation_id="get_production_order_consumption",
)
def get_production_order_consumption(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    branch: str = Query(..., pattern="^(01|02)$"),
    search: str | None = Query(None),
    product: str | None = Query(None),
    date_type: str = Query(
        "emission", pattern="^(emission|finished|appointment)$"
    ),
    status: str | None = Query(None),
    work_center: str | None = Query(None),
    operation: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=50),
    sort_by: str | None = Query(
        None,
        pattern=(
            "^(production_order|product_code|product_description|"
            "status|date)$"
        ),
    ),
    sort_direction: str | None = Query(None, pattern="^(asc|desc)$"),
):
    """Visão operacional R04 — lista de OPs para auditoria de consumo,
    delegada ao produtor consumption-audit da api-delpi."""
    _authorized_user(request)
    access_token = _user_bearer(request)
    period_start, period_end = _period_bounds(period)
    params: dict[str, Any] = {
        "branch": branch,
        "date_type": date_type,
        "period_start": period_start,
        "period_end": period_end,
        "page": page,
        "page_size": page_size,
    }
    for key, value in (
        ("search", search),
        ("product", product),
        ("status", status),
        ("work_center", work_center),
        ("operation", operation),
        ("sort_by", sort_by),
        ("sort_direction", sort_direction),
    ):
        # Chamadas diretas (MCP tool bridge) deixam defaults Query(...) —
        # só strings reais são encaminhadas ao produtor.
        if isinstance(value, str) and value:
            params[key] = value
    try:
        body = ApiDelpiSettlementsGateway().get(
            "/supplies/consumption-audit/orders",
            access_token=access_token,
            params=params,
            timeout_seconds=120,
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(exc, "get_production_order_consumption")
    if not isinstance(body, dict) or body.get("success") is not True:
        return _map_gateway_error(
            DelpiApiGatewayError(
                "Resposta inesperada da origem de dados.",
                status_code=502,
            ),
            "get_production_order_consumption",
        )
    data = body.get("data") or {}
    return ok(
        _projection(data, period=period, branch=branch, date_type=date_type),
        message="Consumo por OP carregado (visão operacional).",
        operation_id="get_production_order_consumption",
    )


@router.get(
    "/competences/{period}/production-order-consumption/{production_order}",
    operation_id="get_production_order_consumption_detail",
)
def get_production_order_consumption_detail(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    production_order: str = Path(),
    branch: str = Query(..., pattern="^(01|02)$"),
    date_type: str = Query(
        "emission", pattern="^(emission|finished|appointment)$"
    ),
):
    """Detalhe OP × operação × componente — mesmo produtor, mesma
    visão operacional R04."""
    _authorized_user(request)
    access_token = _user_bearer(request)
    try:
        body = ApiDelpiSettlementsGateway().get(
            f"/supplies/consumption-audit/orders/{production_order}",
            access_token=access_token,
            params={"branch": branch},
            timeout_seconds=120,
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(
            exc, "get_production_order_consumption_detail"
        )
    if not isinstance(body, dict) or body.get("success") is not True:
        return _map_gateway_error(
            DelpiApiGatewayError(
                "Resposta inesperada da origem de dados.",
                status_code=502,
            ),
            "get_production_order_consumption_detail",
        )
    data = body.get("data") or {}
    return ok(
        _projection(data, period=period, branch=branch, date_type=date_type),
        message="Detalhe de consumo da OP carregado (visão operacional).",
        operation_id="get_production_order_consumption_detail",
    )
