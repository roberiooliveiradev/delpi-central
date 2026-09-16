from __future__ import annotations

from typing import Any

from purchase_requests_app.application.security.purchase_requests_permissions import (
    assert_branch_access,
    assert_branches_access,
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
        branch: str | None = None,
        branches: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        request_number: str | None = None,
        requester_user_ids: list[str] | None = None,
        cost_center: str | None = None,
        cost_centers: list[str] | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
        overall_stage: str | None = None,
        overall_stages: list[str] | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        if not has_access(user):
            raise PermissionError("Sem permissão para acessar solicitações de compra.")
        codes = self._authorized_branches(user, branch=branch, branches=branches)
        resolution, cost_center_codes, scopes = self._resolve_scopes(
            user=user,
            branches=codes,
            cost_center=cost_center,
            cost_centers=cost_centers,
        )
        if cost_center_codes == [] or scopes == []:
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0,
            }
        params = self._gateway_params(
            branches=codes,
            date_from=date_from,
            date_to=date_to,
            request_number=request_number,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
            requester_user_ids=requester_user_ids,
            cost_centers=cost_center_codes,
            scopes=scopes,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )
        payload = self._gateway.list_lines(params=params)
        return self._assemble_page(
            payload,
            resolution=resolution,
            overall_stages=overall_stages,
            overall_stage=overall_stage,
            page=page,
            page_size=page_size,
        )

    def export(
        self,
        *,
        user,
        branch: str | None = None,
        branches: list[str] | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        request_number: str | None = None,
        requester_user_ids: list[str] | None = None,
        cost_center: str | None = None,
        cost_centers: list[str] | None = None,
        product_code: str | None = None,
        supplier_code: str | None = None,
        order_number: str | None = None,
        overall_stage: str | None = None,
        overall_stages: list[str] | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
    ) -> dict[str, Any]:
        if not has_access(user):
            raise PermissionError("Sem permissão para acessar solicitações de compra.")
        codes = self._authorized_branches(user, branch=branch, branches=branches)
        resolution, cost_center_codes, scopes = self._resolve_scopes(
            user=user,
            branches=codes,
            cost_center=cost_center,
            cost_centers=cost_centers,
        )
        if cost_center_codes == [] or scopes == []:
            return {"items": [], "total": 0}
        params = self._gateway_params(
            branches=codes,
            date_from=date_from,
            date_to=date_to,
            request_number=request_number,
            product_code=product_code,
            supplier_code=supplier_code,
            order_number=order_number,
            requester_user_ids=requester_user_ids,
            cost_centers=cost_center_codes,
            scopes=scopes,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        payload = self._gateway.export_lines(params=params)
        assembled = self._assemble_page(
            payload,
            resolution=resolution,
            overall_stages=overall_stages,
            overall_stage=overall_stage,
            page=1,
            page_size=len(payload.get("items") or []) or 1,
        )
        items = assembled["items"]
        return {"items": items, "total": len(items)}

    def _authorized_branches(
        self,
        user,
        *,
        branch: str | None,
        branches: list[str] | None,
    ) -> list[str]:
        if branches:
            return assert_branches_access(user, branches)
        if branch:
            assert_branch_access(user, branch)
            return [branch]
        raise PermissionError("Sem permissão para acessar dados da filial.")

    def _resolve_scopes(
        self,
        *,
        user,
        branches: list[str],
        cost_center: str | None,
        cost_centers: list[str] | None,
    ):
        scope_rows = self._scope_repository.list_active_cost_centers_for_user(
            str(getattr(user, "id", "") or getattr(user, "sub", ""))
        )
        if len(branches) == 1:
            resolution = self._scope_resolver.resolve(
                user=user,
                branch=branches[0],
                explicit_cost_center=cost_center,
                explicit_cost_centers=cost_centers,
                scope_rows=scope_rows,
            )
            effective = self._scope_resolver.effective_cost_centers(
                resolution,
                branch=branches[0],
                explicit_cost_center=cost_center,
                explicit_cost_centers=cost_centers,
            )
            if effective == []:
                return resolution, [], None
            return resolution, effective, None
        resolution = self._scope_resolver.resolve_for_branches(
            user=user,
            branches=branches,
            explicit_cost_center=cost_center,
            explicit_cost_centers=cost_centers,
            scope_rows=scope_rows,
        )
        scopes = self._scope_resolver.effective_cost_center_scopes(
            resolution,
            branches=branches,
            explicit_cost_center=cost_center,
            explicit_cost_centers=cost_centers,
        )
        return resolution, None, scopes

    def _gateway_params(
        self,
        *,
        branches: list[str],
        date_from: str | None,
        date_to: str | None,
        request_number: str | None,
        product_code: str | None,
        supplier_code: str | None,
        order_number: str | None,
        requester_user_ids: list[str] | None,
        cost_centers: list[str] | None,
        scopes: list[str] | None,
        sort_by: str | None,
        sort_dir: str | None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "branch": branches,
            "date_from": date_from,
            "date_to": date_to,
            "request_number": request_number,
            "product_code": product_code,
            "supplier_code": supplier_code,
            "order_number": order_number,
        }
        if sort_by:
            params["sort_by"] = sort_by
            params["sort_dir"] = sort_dir or "desc"
        if page is not None:
            params["page"] = str(page)
        if page_size is not None:
            params["page_size"] = str(page_size)
        if scopes is not None:
            params["cc_scope"] = scopes
        elif cost_centers is not None:
            params["cost_centers"] = cost_centers
        if requester_user_ids:
            cleaned = [item.strip() for item in requester_user_ids if item and item.strip()]
            if cleaned:
                params["requester_protheus_user_id"] = cleaned
        return params

    def _assemble_page(
        self,
        payload: dict[str, Any],
        *,
        resolution,
        overall_stages: list[str] | None,
        overall_stage: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        lines = payload.get("items") or []
        lines = self._aggregation.filter_authorized_lines(
            lines,
            resolution=resolution,
        )
        items = self._aggregation.build_list_line_items(lines)
        stages = _normalize_overall_stages(overall_stages, overall_stage)
        if stages:
            allowed_stages = set(stages)
            items = [
                item
                for item in items
                if (item.get("derived") or {}).get("overall_stage") in allowed_stages
            ]
        return {
            "items": items,
            "page": payload.get("page", page),
            "page_size": payload.get("page_size", page_size),
            "total": payload.get("total", len(items)),
            "total_pages": payload.get("total_pages", 0),
        }


def _normalize_overall_stages(
    overall_stages: list[str] | None,
    overall_stage: str | None,
) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for raw in [*(overall_stages or []), overall_stage or ""]:
        for part in str(raw or "").split(","):
            stage = part.strip()
            if stage and stage not in seen:
                seen.add(stage)
                values.append(stage)
    return values
