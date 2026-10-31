"""R12/R15 governed closing-state view (doc 129).

BFF owns: human principal + ``controllership-finance.access`` (Core
effective permissions), delegation of the user Bearer, the governed node
projection and typed error passthrough. Markers stay raw upstream —
nothing here writes the ERP or the P3 canonical state.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query, Request

from controllership_finance_app.application.services.closing_state_projection import (
    build_closing_state_projection,
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

router = APIRouter(prefix="/closing", tags=["Closing State"])

PERIOD_PATTERN = r"^\d{4}-(0[1-9]|1[0-2])$"


@router.get(
    "/competences/{period}/cost-closing-state",
    operation_id="get_cost_closing_state",
)
def get_cost_closing_state(
    request: Request,
    period: str = Path(pattern=PERIOD_PATTERN),
    branch: str = Query("all", pattern="^(all|01|02)$"),
):
    """Projeção governada de estado R12/R15 por competência/filial —
    marcadores observados, nunca homologação ou execução."""
    _authorized_user(request)
    access_token = _user_bearer(request)
    try:
        body = ApiDelpiSettlementsGateway().get(
            "/financeiro/closing-state",
            access_token=access_token,
            params={"period": period, "branch": branch},
        )
    except DelpiApiGatewayError as exc:
        return _map_gateway_error(exc, "get_cost_closing_state")
    if not isinstance(body, dict) or body.get("success") is not True:
        return _map_gateway_error(
            DelpiApiGatewayError(
                "Resposta inesperada da origem de dados.",
                status_code=502,
            ),
            "get_cost_closing_state",
        )
    data = body.get("data") or {}
    projection = build_closing_state_projection(
        period=data.get("period") or period,
        reference_date=data.get("referenceDate") or "",
        branch_payloads=data.get("branches") or {},
    )
    return ok(
        {
            "report": data.get("report") or "cost-closing-state",
            "observedAt": data.get("observedAt"),
            "evidenceWindow": data.get("evidenceWindow"),
            "provenance": data.get("provenance"),
            **projection,
        },
        message="Estado de fechamento carregado.",
        operation_id="get_cost_closing_state",
    )
