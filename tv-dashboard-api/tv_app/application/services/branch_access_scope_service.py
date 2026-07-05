from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from delpi_auth.authz_core import has_permission

from tv_app.application.security.tv_dashboard_permissions import (
    TV_VIEW_CONSOLIDATED,
    branch_codes_from_permissions,
)
from tv_app.application.services.tv_dashboard_content_service import (
    allowed_branches,
    branch_rejection_message,
    message,
)
from tv_app.core.security import TV_ADMIN


def _normalize_branch(value: str | None) -> str | None:
    if value is None:
        return None
    code = str(value).strip()
    return code or None


@dataclass(frozen=True)
class BranchAccessScope:
    mode: str
    allowed_branches: frozenset[str]
    allow_consolidated: bool

    @property
    def is_unrestricted(self) -> bool:
        return self.mode == "unrestricted"

    def meta(self) -> dict[str, object]:
        return {
            "mode": self.mode,
            "allowConsolidated": self.allow_consolidated,
            "branches": self.branch_options(),
        }

    def branch_options(self) -> list[str]:
        static = allowed_branches()
        if self.is_unrestricted:
            return static
        jwt_branches = sorted(self.allowed_branches)
        if static:
            return sorted(set(static) & set(jwt_branches))
        return jwt_branches


class BranchAccessScopeService:
    def resolve(self, user: Any | None) -> BranchAccessScope:
        if user is None or getattr(user, "is_superadmin", False):
            return BranchAccessScope(
                mode="unrestricted",
                allowed_branches=frozenset(),
                allow_consolidated=True,
            )
        if has_permission(user, TV_ADMIN):
            return BranchAccessScope(
                mode="unrestricted",
                allowed_branches=frozenset(),
                allow_consolidated=True,
            )

        permissions = list(getattr(user, "permissions", []) or [])
        branch_codes = branch_codes_from_permissions(permissions)
        if not branch_codes:
            return BranchAccessScope(
                mode="unrestricted",
                allowed_branches=frozenset(),
                allow_consolidated=True,
            )

        allow_consolidated = TV_VIEW_CONSOLIDATED in permissions
        return BranchAccessScope(
            mode="scoped",
            allowed_branches=frozenset(branch_codes),
            allow_consolidated=allow_consolidated,
        )

    def can_use_branch(self, scope: BranchAccessScope, branch: str | None) -> bool:
        code = _normalize_branch(branch)
        if not code:
            return scope.allow_consolidated or scope.is_unrestricted
        static = allowed_branches()
        if static and code not in static:
            return False
        if scope.is_unrestricted:
            return True
        return code in scope.allowed_branches

    def assert_branch_allowed(self, scope: BranchAccessScope, branch: str | None) -> None:
        if self.can_use_branch(scope, branch):
            return
        code = _normalize_branch(branch)
        if not code:
            raise ValueError(message("consolidatedNotAllowed"))
        raise ValueError(branch_rejection_message())
