from __future__ import annotations

from typing import Any

from tv_app.application.services.branch_access_scope_service import (
    BranchAccessScope,
    BranchAccessScopeService,
)
from tv_app.application.services.tv_dashboard_content_service import (
    allowed_branches,
    branch_rejection_message,
)

_scope_service = BranchAccessScopeService()


def resolve_branch_access_scope(user: Any | None) -> BranchAccessScope:
    return _scope_service.resolve(user)


def validate_native_branch(
    config: dict[str, Any] | None,
    *,
    user: Any | None = None,
) -> None:
    cfg = config or {}
    branch = cfg.get("branch")
    if branch is None or branch == "":
        scope = resolve_branch_access_scope(user)
        _scope_service.assert_branch_allowed(scope, None)
        return
    branch_code = str(branch).strip()
    if not branch_code:
        scope = resolve_branch_access_scope(user)
        _scope_service.assert_branch_allowed(scope, None)
        return
    static_allowed = allowed_branches()
    if static_allowed and branch_code not in static_allowed:
        raise ValueError(branch_rejection_message())
    scope = resolve_branch_access_scope(user)
    _scope_service.assert_branch_allowed(scope, branch_code)
