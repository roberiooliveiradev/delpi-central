from __future__ import annotations

from financial_app.application.services.cost_center_service import InvalidCostCenterQuery
from financial_app.application.services.delinquency_service import InvalidDelinquencyQuery
from financial_app.core.responses import fail
from financial_app.domain.errors import (
    BranchAccessDenied,
    DelpiGatewayError,
    InvalidBranch,
    InvalidPeriod,
)


def fail_from_exception(exc: Exception):
    if isinstance(exc, (InvalidBranch, InvalidPeriod, InvalidDelinquencyQuery, InvalidCostCenterQuery)):
        return fail(str(exc), 400)
    if isinstance(exc, (BranchAccessDenied, PermissionError)):
        return fail(str(exc), 403)
    if isinstance(exc, DelpiGatewayError):
        return fail(str(exc), 502)
    raise exc
