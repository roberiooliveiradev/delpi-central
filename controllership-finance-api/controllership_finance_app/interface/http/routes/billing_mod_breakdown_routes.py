"""R09 governed billing × MOD breakdown view (doc 144 — DR-1/DR-2).

BFF owns: human principal + ``controllership-finance.access`` (Core
effective permissions), delegation of the user Bearer, the officiality/
parity-evidence projection and typed error passthrough. All Protheus
data comes from api-delpi — nothing here recomputes MOD, hours or
costs, and unavailable fields stay typed absence upstream.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query, Request

from controllership_finance_app.application.services.billing_mod_breakdown_projection import (
    build_billing_mod_breakdown_projection,
)
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

router = APIRouter(prefix="/closing", tags=["Billing MOD Breakdown"])

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get(
    "/competences/{period}/billing-mod-breakdown",
    operation_id="get_billing_mod_breakdown",
)
def get_billing_mod_breakdown(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    branch: str = Query("all", pattern="^(all|01|02)$"),
):
    """Visão operacional governada R09 — faturamento × MOD por âncora
    PA, com proveniência, estados de ausência e evidência histórica de
    paridade. Paridade oficial pendente (DR-3)."""
    _authorized_user(request)
    access_token = _user_bearer(request)
    try:
        body = ApiDelpiSettlementsGateway().get(
            "/financeiro/billing-mod-breakdown",
            access_token=access_token,
            params={"period": period, "branch": branch},
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(exc, "get_billing_mod_breakdown")
    if not isinstance(body, dict) or body.get("success") is not True:
        return _map_gateway_error(
            DelpiApiGatewayError(
                "Resposta inesperada da origem de dados.",
                status_code=502,
            ),
            "get_billing_mod_breakdown",
        )
    data = body.get("data") or {}
    projection = build_billing_mod_breakdown_projection(data)
    return ok(
        projection,
        message="Faturamento × MOD carregado (visão operacional).",
        operation_id="get_billing_mod_breakdown",
    )
