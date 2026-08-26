from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from purchase_requests_app.application.security.purchase_requests_permissions import (
    assert_branch_access,
    has_admin,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)


def _default_admin_period() -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=365)
    return start.isoformat(), end.isoformat()


class ListAdminProtheusUsersUseCase:
    def __init__(self, *, gateway: DelpiPurchaseRequestsGateway | None = None) -> None:
        self._gateway = gateway or DelpiPurchaseRequestsGateway()

    def execute(
        self,
        *,
        user,
        branch: str,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict[str, Any]:
        if not has_admin(user):
            raise PermissionError("Sem permissão administrativa.")
        assert_branch_access(user, branch)
        period_from, period_to = _default_admin_period()
        params: dict[str, Any] = {
            "branch": branch,
            "date_from": date_from or period_from,
            "date_to": date_to or period_to,
        }
        payload = self._gateway.list_requesters(params=params)
        return {"items": payload.get("items") or []}
