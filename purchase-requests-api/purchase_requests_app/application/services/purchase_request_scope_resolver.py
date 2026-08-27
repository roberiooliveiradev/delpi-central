from __future__ import annotations

from purchase_requests_app.application.security.purchase_requests_permissions import (
    has_view_all,
)
from purchase_requests_app.domain.services.purchase_request_domain_service import (
    CostCenterScope,
    ScopeResolution,
)


def normalize_cost_center_codes(
    explicit_cost_center: str | None = None,
    explicit_cost_centers: list[str] | None = None,
) -> list[str]:
    codes: list[str] = []
    seen: set[str] = set()
    for raw in [*(explicit_cost_centers or []), explicit_cost_center or ""]:
        for part in str(raw or "").split(","):
            code = part.strip()
            if code and code not in seen:
                seen.add(code)
                codes.append(code)
    return codes


class PurchaseRequestScopeResolver:
    def resolve(
        self,
        *,
        user,
        branch: str,
        explicit_cost_center: str | None = None,
        explicit_cost_centers: list[str] | None = None,
        scope_rows: list[dict] | None = None,
    ) -> ScopeResolution:
        view_all = has_view_all(user)
        if view_all:
            resolution = ScopeResolution(view_all=True, allowed_cost_centers=frozenset())
        else:
            allowed = self._union_active_scopes(scope_rows or [])
            branch_allowed = {
                item
                for item in allowed
                if item.branch == branch
            }
            resolution = ScopeResolution(view_all=False, allowed_cost_centers=frozenset(branch_allowed))

        for code in normalize_cost_center_codes(
            explicit_cost_center=explicit_cost_center,
            explicit_cost_centers=explicit_cost_centers,
        ):
            if not resolution.view_all and not resolution.allows(branch, code):
                raise PermissionError(
                    f"Sem permissão para consultar o centro de custo {code}."
                )
        return resolution

    def effective_cost_centers(
        self,
        resolution: ScopeResolution,
        *,
        branch: str,
        explicit_cost_center: str | None = None,
        explicit_cost_centers: list[str] | None = None,
    ) -> list[str] | None:
        codes = normalize_cost_center_codes(
            explicit_cost_center=explicit_cost_center,
            explicit_cost_centers=explicit_cost_centers,
        )
        if resolution.view_all:
            return codes or None
        allowed_codes = resolution.cost_center_codes_for_branch(branch)
        if not allowed_codes:
            return []
        if codes:
            forbidden = [code for code in codes if code not in allowed_codes]
            if forbidden:
                raise PermissionError(
                    f"Sem permissão para consultar o centro de custo {forbidden[0]}."
                )
            return codes
        return allowed_codes

    @staticmethod
    def _union_active_scopes(rows: list[dict]) -> set[CostCenterScope]:
        result: set[CostCenterScope] = set()
        for row in rows:
            branch = str(row.get("branch") or "").strip()
            code = str(row.get("cost_center_code") or "").strip()
            if branch and code:
                result.add(CostCenterScope(branch=branch, cost_center_code=code))
        return result
