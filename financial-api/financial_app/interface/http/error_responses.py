from __future__ import annotations

from typing import Any, Callable

from fastapi.responses import JSONResponse

from financial_app.core.responses import fail, ok
from financial_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    FinancialError,
    InvalidBranch,
    InvalidPeriod,
    StrategicIndicatorsGatewayError,
)

_STATUS_BY_ERROR: tuple[tuple[type[Exception], int], ...] = (
    (PermissionError, 403),
    (BranchAccessDenied, 403),
    (InvalidBranch, 400),
    (InvalidPeriod, 400),
    (DelpiGatewayError, 502),
    (StrategicIndicatorsGatewayError, 502),
)


def domain_error_response(exc: Exception) -> JSONResponse | None:
    """Traduz erro de domínio em envelope HTTP. ``None`` = erro não mapeado."""
    for error_type, status_code in _STATUS_BY_ERROR:
        if isinstance(exc, error_type):
            return fail(str(exc), status_code)
    # Erros de validação de query do próprio portal herdam FinancialError.
    if isinstance(exc, FinancialError):
        return fail(str(exc), 400)
    return None


def respond(producer: Callable[[], Any], *, message: str = "OK") -> JSONResponse:
    """Envelopa o resultado do serviço e traduz erros de domínio em HTTP."""
    try:
        return ok(producer(), message=message)
    except Exception as exc:  # noqa: BLE001
        mapped = domain_error_response(exc)
        if mapped is None:
            raise
        return mapped
