"""GET/PUT /forecast/current — declared FCT (not TOTVS / not OP forecast)."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel, Field

from commercial_app.application.security.auth_dependencies import require_any_permission
from commercial_app.application.security.commercial_permissions import (
    COMMERCIAL_READ_PERMISSIONS,
)
from commercial_app.application.use_cases.get_put_forecast_declaration import (
    GetPutForecastDeclarationUseCase,
)
from commercial_app.core.auth_actor import actor_sub_from_request
from commercial_app.core.responses import fail, ok
from commercial_app.infrastructure.persistence.repositories.postgres_forecast_declaration_repository import (
    PostgresForecastDeclarationRepository,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/forecast", tags=["Forecast"])


class PutForecastBody(BaseModel):
    declaredValue: float = Field(ge=0)
    cycleYear: int | None = None
    cycleMonth: int | None = Field(default=None, ge=1, le=12)
    portfolioId: str | None = None


def _use_case() -> GetPutForecastDeclarationUseCase:
    return GetPutForecastDeclarationUseCase(PostgresForecastDeclarationRepository())


@router.get("/current", operation_id="get_current_forecast")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def get_current_forecast(
    request: Request,
    cycle_year: int | None = Query(default=None),
    cycle_month: int | None = Query(default=None, ge=1, le=12),
    portfolio_id: str | None = Query(default=None),
):
    try:
        data = _use_case().get(
            cycle_year=cycle_year,
            cycle_month=cycle_month,
            portfolio_id=portfolio_id,
        )
        return ok(data, message="Previsão declarada carregada.", operation_id="get_current_forecast")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="get_current_forecast")
    except Exception:
        logger.exception("get_current_forecast_failed")
        return fail("Erro ao carregar previsão declarada.", 500, operation_id="get_current_forecast")


@router.put("/current", operation_id="put_current_forecast")
@require_any_permission(*COMMERCIAL_READ_PERMISSIONS)
def put_current_forecast(request: Request, body: PutForecastBody):
    user_id = actor_sub_from_request(request) or ""
    try:
        data = _use_case().put(
            declared_value=body.declaredValue,
            updated_by=user_id,
            cycle_year=body.cycleYear,
            cycle_month=body.cycleMonth,
            portfolio_id=body.portfolioId,
        )
        return ok(data, message="Previsão declarada salva.", operation_id="put_current_forecast")
    except ValueError as exc:
        return fail(str(exc), 400, operation_id="put_current_forecast")
    except Exception:
        logger.exception("put_current_forecast_failed")
        return fail("Erro ao salvar previsão declarada.", 500, operation_id="put_current_forecast")
