from __future__ import annotations

from typing import Any

from purchase_requests_app.application.security.purchase_requests_permissions import (
    assert_branch_access,
    has_access,
)
from purchase_requests_app.application.services.purchase_request_aggregation_service import (
    PurchaseRequestAggregationService,
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


class ListPurchaseRequestsUseCase:
    def __init__(
        self,
        *,
        gateway: DelpiPurchaseRequestsGateway | None = None,
        scope_repository: VisibilityScopeRepository | None = None,
        scope_resolver: PurchaseRequestScopeResolver | None = None,
        aggregation: PurchaseRequestAggregationService | None = None,
    ) -> None:
        self._gateway = gateway or DelpiPurchaseRequestsGateway()
        self._scope_repository = scope_repository or VisibilityScopeRepository()
        self._scope_resolver = scope_resolver or PurchaseRequestScopeResolver()
        self._aggregation = aggregation or PurchaseRequestAggregationService()

    def execute(
        self,
        *,
        user,
        branch: str,
        date_from: str | None = None,
        date_to: str | None = None,
        request_number: str | None = None,
        requester_user_ids: list[str] | None = None,
        cost_center: str | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
        overall_stage: str | None = None,
        page: int = 1,
        page_size: int = 50,
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
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0,
            }
        params: dict[str, Any] = {
            "branch": branch,
            "date_from": date_from,
            "date_to": date_to,
            "request_number": request_number,
            "product_code": product_code,
            "supplier_code": supplier_code,
            "order_number": order_number,
            "page": str(page),
            "page_size": str(page_size),
        }
        if effective_ccs is not None:
            params["cost_centers"] = effective_ccs
        if requester_user_ids:
            cleaned = [item.strip() for item in requester_user_ids if item and item.strip()]
            if cleaned:
                params["requester_protheus_user_id"] = cleaned
        payload = self._gateway.list_lines(params=params)
        lines = payload.get("items") or []
        lines = self._aggregation.filter_authorized_lines(
            lines,
            branch=branch,
            resolution=resolution,
        )
        items = self._aggregation.build_list_line_items(lines)
        if overall_stage:
            items = [
                item
                for item in items
                if (item.get("derived") or {}).get("overall_stage") == overall_stage
            ]
        return {
            "items": items,
            "page": payload.get("page", page),
            "page_size": payload.get("page_size", page_size),
            "total": payload.get("total", len(lines)),
            "total_pages": payload.get("total_pages", 0),
        }
