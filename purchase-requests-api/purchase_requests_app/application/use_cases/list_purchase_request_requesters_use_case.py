from __future__ import annotations

from typing import Any

from purchase_requests_app.application.security.purchase_requests_permissions import (
    assert_branch_access,
    has_access,
)
from purchase_requests_app.application.services.purchase_request_scope_resolver import (
    PurchaseRequestScopeResolver,
)
from purchase_requests_app.infrastructure.gateways.delpi_purchase_requests_gateway import (
    DelpiPurchaseRequestsGateway,
)
from purchase_requests_app.infrastructure.persistence.repositories.visibility_scope_repository import (
    VisibilityScopeRepository,
)


class ListPurchaseRequestRequestersUseCase:
    def __init__(
        self,
        *,
        gateway: DelpiPurchaseRequestsGateway | None = None,
        scope_repository: VisibilityScopeRepository | None = None,
        scope_resolver: PurchaseRequestScopeResolver | None = None,
    ) -> None:
        self._gateway = gateway or DelpiPurchaseRequestsGateway()
        self._scope_repository = scope_repository or VisibilityScopeRepository()
        self._scope_resolver = scope_resolver or PurchaseRequestScopeResolver()

    def execute(
        self,
        *,
        user,
        branch: str,
        date_from: str | None = None,
        date_to: str | None = None,
        cost_center: str | None = None,
        request_number: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
    ) -> dict[str, Any]:
        if not has_access(user):
            raise PermissionError("Sem permissão para acessar solicitações de compra.")
        assert_branch_access(user, branch)
        scope_rows = self._scope_repository.list_active_cost_centers_for_user(
            str(getattr(user, "id", "") or getattr(user, "sub", ""))
        )
        resolution = self._scope_resolver.resolve(
            user=user,
            branch=branch,
            explicit_cost_center=cost_center,
            scope_rows=scope_rows,
        )
        effective_ccs = self._scope_resolver.effective_cost_centers(
            resolution,
            branch=branch,
            explicit_cost_center=cost_center,
        )
        if effective_ccs == []:
            return {"items": []}
        params: dict[str, Any] = {
            "branch": branch,
            "date_from": date_from,
            "date_to": date_to,
            "request_number": request_number,
            "product_code": product_code,
            "supplier_code": supplier_code,
            "order_number": order_number,
        }
        if effective_ccs is not None:
            params["cost_centers"] = effective_ccs
        payload = self._gateway.list_requesters(params=params)
        return {"items": payload.get("items") or []}
