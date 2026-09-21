from __future__ import annotations

import math
from typing import Any

from purchase_requests_app.application.security.purchase_requests_permissions import (
    assert_branch_access,
    assert_branches_access,
    has_access,
)
from purchase_requests_app.application.security.supplies_portal_context import (
    authorize_portal_branches,
    is_trusted_supplies_bff_call,
)
from purchase_requests_app.application.services.purchase_request_aggregation_service import (
    DERIVED_STAGE_MAX_HEADERS,
    DERIVED_STAGE_PAGE_SIZE,
    DERIVED_STAGE_TOO_LARGE_MESSAGE,
    GATEWAY_SORT_FIELDS,
    LOCAL_SORT_FIELDS,
    SUMMARY_TOO_LARGE_MESSAGE,
    PurchaseRequestAggregationService,
    normalize_list_sort_by,
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
        portal = is_trusted_supplies_bff_call()
        if not portal and not has_access(user):
            raise PermissionError("Sem permissão para acessar solicitações de compra.")
        codes = self._authorized_branches(
            user,
            branch=branch,
            branches=branches,
            portal=portal,
        )
        resolution, cost_center_codes, scopes = self._resolve_scopes(
            user=user,
            branches=codes,
            cost_center=cost_center,
            cost_centers=cost_centers,
            portal=portal,
        )
        if cost_center_codes == [] or scopes == []:
            return {
                "items": [],
                "page": page,
                "page_size": page_size,
                "total": 0,
                "total_pages": 0,
            }
        normalized_sort = normalize_list_sort_by(sort_by)
        self._assert_sort(normalized_sort, sort_dir)
        stages = _normalize_overall_stages(overall_stages, overall_stage)
        if normalized_sort == "overall_stage" or stages:
            # Derived stage is owner-local. Collect the capped header universe
            # before the page cut so the filter is not limited to one upstream page.
            gateway_sort = (
                None
                if normalized_sort == "overall_stage"
                else (normalized_sort if normalized_sort in GATEWAY_SORT_FIELDS else None)
            )
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
                sort_by=gateway_sort,
                sort_dir=sort_dir if gateway_sort else None,
            )
            payload = self._collect_lines_for_derived_stage(
                params=params,
                too_large_message=DERIVED_STAGE_TOO_LARGE_MESSAGE,
            )
            return self._assemble_derived_page(
                payload,
                resolution=resolution,
                stages=stages,
                sort_by=normalized_sort,
                sort_dir=sort_dir,
                page=page,
                page_size=page_size,
            )

        gateway_sort = normalized_sort if normalized_sort in GATEWAY_SORT_FIELDS else None
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
            sort_by=gateway_sort,
            sort_dir=sort_dir if gateway_sort else None,
            page=page,
            page_size=page_size,
        )
        payload = self._gateway.list_lines(params=params)
        return self._assemble_page(
            payload,
            resolution=resolution,
            overall_stages=overall_stages,
            overall_stage=overall_stage,
            sort_by=normalized_sort,
            sort_dir=sort_dir,
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
        portal = is_trusted_supplies_bff_call()
        if not portal and not has_access(user):
            raise PermissionError("Sem permissão para acessar solicitações de compra.")
        codes = self._authorized_branches(
            user,
            branch=branch,
            branches=branches,
            portal=portal,
        )
        resolution, cost_center_codes, scopes = self._resolve_scopes(
            user=user,
            branches=codes,
            cost_center=cost_center,
            cost_centers=cost_centers,
            portal=portal,
        )
        if cost_center_codes == [] or scopes == []:
            return {"items": [], "total": 0}
        normalized_sort = normalize_list_sort_by(sort_by)
        self._assert_sort(normalized_sort, sort_dir)
        gateway_sort = (
            None
            if normalized_sort == "overall_stage"
            else (normalized_sort if normalized_sort in GATEWAY_SORT_FIELDS else None)
        )
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
            sort_by=gateway_sort,
            sort_dir=sort_dir if gateway_sort else None,
        )
        payload = self._gateway.export_lines(params=params)
        lines = self._aggregation.filter_authorized_lines(
            payload.get("items") or [],
            resolution=resolution,
        )
        stages = _normalize_overall_stages(overall_stages, overall_stage)
        if stages:
            lines = self._aggregation.lines_matching_header_stages(lines, set(stages))
        items = self._aggregation.build_list_line_items(
            lines,
            sort_by=normalized_sort,
            sort_dir=sort_dir,
        )
        return {"items": items, "total": len(items)}

    def summarize(
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
    ) -> dict[str, Any]:
        """Header summary for the base filters. The stage chip is ignored on purpose."""
        del overall_stage, overall_stages
        portal = is_trusted_supplies_bff_call()
        if not portal and not has_access(user):
            raise PermissionError("Sem permissão para acessar solicitações de compra.")
        codes = self._authorized_branches(
            user,
            branch=branch,
            branches=branches,
            portal=portal,
        )
        resolution, cost_center_codes, scopes = self._resolve_scopes(
            user=user,
            branches=codes,
            cost_center=cost_center,
            cost_centers=cost_centers,
            portal=portal,
        )
        if cost_center_codes == [] or scopes == []:
            return self._aggregation.summarize_lines([])
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
            sort_by=None,
            sort_dir=None,
        )
        payload = self._collect_lines_for_derived_stage(
            params=params,
            too_large_message=SUMMARY_TOO_LARGE_MESSAGE,
        )
        lines = self._aggregation.filter_authorized_lines(
            payload.get("items") or [],
            resolution=resolution,
        )
        return self._aggregation.summarize_lines(lines)

    @staticmethod
    def _assert_sort(sort_by: str | None, sort_dir: str | None) -> None:
        if sort_by is None:
            return
        if sort_by not in GATEWAY_SORT_FIELDS and sort_by not in LOCAL_SORT_FIELDS:
            raise ValueError("Invalid sort_by")
        if sort_dir is not None and (sort_dir or "").strip().lower() not in {"", "asc", "desc"}:
            raise ValueError("Invalid sort_dir")

    def _authorized_branches(
        self,
        user,
        *,
        branch: str | None,
        branches: list[str] | None,
        portal: bool,
    ) -> list[str]:
        requested = list(branches or [])
        if not requested and branch:
            requested = [branch]
        if portal:
            return authorize_portal_branches(requested)
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
        portal: bool,
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
                portal_global=portal,
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
            portal_global=portal,
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

    def _collect_lines_for_derived_stage(
        self,
        *,
        params: dict[str, Any],
        too_large_message: str,
    ) -> dict[str, Any]:
        """Fetch list_lines pages for derived-stage sort, filter or summary.

        Caps by header total from the first page. Does not use uncapped export.
        """
        first_params = {
            **params,
            "page": "1",
            "page_size": str(DERIVED_STAGE_PAGE_SIZE),
        }
        first = self._gateway.list_lines(params=first_params)
        try:
            total = int(first.get("total") or 0)
        except (TypeError, ValueError):
            total = 0
        if total > DERIVED_STAGE_MAX_HEADERS:
            raise ValueError(too_large_message)

        items: list[Any] = list(first.get("items") or [])
        try:
            total_pages = int(first.get("total_pages") or 0)
        except (TypeError, ValueError):
            total_pages = 0
        if total_pages <= 0 and total > 0:
            total_pages = math.ceil(total / DERIVED_STAGE_PAGE_SIZE)

        for page_num in range(2, total_pages + 1):
            page_params = {
                **params,
                "page": str(page_num),
                "page_size": str(DERIVED_STAGE_PAGE_SIZE),
            }
            payload = self._gateway.list_lines(params=page_params)
            items.extend(payload.get("items") or [])

        return {"items": items, "total": total}

    def _assemble_page(
        self,
        payload: dict[str, Any],
        *,
        resolution,
        overall_stages: list[str] | None,
        overall_stage: str | None,
        sort_by: str | None,
        sort_dir: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        lines = payload.get("items") or []
        lines = self._aggregation.filter_authorized_lines(
            lines,
            resolution=resolution,
        )
        items = self._aggregation.build_list_line_items(
            lines,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
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

    def _assemble_derived_page(
        self,
        payload: dict[str, Any],
        *,
        resolution,
        stages: list[str],
        sort_by: str | None,
        sort_dir: str | None,
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        lines = self._aggregation.filter_authorized_lines(
            payload.get("items") or [],
            resolution=resolution,
        )
        return self._aggregation.page_by_header(
            lines,
            allowed_stages=set(stages) if stages else None,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            page_size=page_size,
        )


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
