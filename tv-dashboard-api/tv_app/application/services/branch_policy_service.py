from __future__ import annotations

from typing import Any

from tv_app.application.services.branch_access_scope_service import (
    BranchAccessScope,
    BranchAccessScopeService,
)
from tv_app.application.services.tv_dashboard_content_service import (
    allowed_branches,
    branch_policy_setting,
    branch_rejection_message,
)

_scope_service = BranchAccessScopeService()
_DEFAULT_BRANCH_PARAM_ALIASES = ("branch", "branch_code", "filial", "filial_id")


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


def route_branch_param_aliases(route: dict[str, Any] | None) -> tuple[str, ...]:
    constraints = route.get("tvConstraints") if isinstance(route, dict) else None
    curated = constraints.get("branchParamAliases") if isinstance(constraints, dict) else None
    configured = branch_policy_setting("canonicalParamAliases", _DEFAULT_BRANCH_PARAM_ALIASES)
    raw = curated if isinstance(curated, list) and curated else configured
    aliases = tuple(
        dict.fromkeys(
            str(item).strip()
            for item in (raw if isinstance(raw, list | tuple) else _DEFAULT_BRANCH_PARAM_ALIASES)
            if str(item).strip()
        )
    )
    return aliases or _DEFAULT_BRANCH_PARAM_ALIASES


def resolve_route_branch(
    route: dict[str, Any] | None,
    params: dict[str, Any] | None,
) -> str | None:
    values = params if isinstance(params, dict) else {}
    for alias in route_branch_param_aliases(route):
        value = values.get(alias)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def validate_data_route_branch(
    route: dict[str, Any] | None,
    params: dict[str, Any] | None,
    *,
    user: Any | None = None,
) -> None:
    """Enforcement declarativo; fallback mantém rotas ainda não curadas."""

    constraints = route.get("tvConstraints") if isinstance(route, dict) else None
    marker = constraints.get("requiresBranchPermission") if isinstance(constraints, dict) else None
    if marker is False:
        return
    if marker is True:
        validate_native_branch({"branch": resolve_route_branch(route, params)}, user=user)
        return
    if bool(branch_policy_setting("compatibilityFallbackForUncuratedRoutes", True)):
        # Compatibilidade histórica: apenas `branch` era reconhecido nas rotas sem curadoria.
        values = params if isinstance(params, dict) else {}
        validate_native_branch({"branch": values.get("branch")}, user=user)
