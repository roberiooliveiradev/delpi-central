from __future__ import annotations

from delpi_auth.authz_core import has_permission

from requests_app.domain.entities import Actor, RequestType

ACCESS_PERMISSION = "my-requests.access"
VIEW_ALL_PERMISSION = "my-requests.view-all"
MANAGE_PERMISSION = "my-requests.manage"

BRANCH_VIEW_PERMISSIONS: dict[str, str] = {
    "01": "my-requests.view.filial-01",
    "02": "my-requests.view.filial-02",
}

VALID_BRANCHES = frozenset(BRANCH_VIEW_PERMISSIONS)


def _user_id(user) -> str:
    return str(getattr(user, "id", "") or getattr(user, "sub", "") or "unknown")


def _user_name(user) -> str:
    raw = getattr(user, "name", None) or getattr(user, "email", None) or "Usuário"
    return str(raw)


def branch_codes_for(user) -> frozenset[str]:
    codes: set[str] = set()
    for branch, permission in BRANCH_VIEW_PERMISSIONS.items():
        if has_permission(user, permission):
            codes.add(branch)
    return frozenset(codes)


def actor_for(user, request_type: RequestType | None = None) -> Actor:
    prefix = (request_type.permission_prefix if request_type else "my-requests").rstrip(".")
    return Actor(
        user_id=_user_id(user),
        user_name=_user_name(user),
        has_access=bool(
            has_permission(user, ACCESS_PERMISSION)
            or has_permission(user, VIEW_ALL_PERMISSION)
            or has_permission(user, MANAGE_PERMISSION)
            or (
                request_type is not None
                and (
                    has_permission(user, f"{prefix}.create")
                    or has_permission(user, f"{prefix}.process")
                )
            )
        ),
        has_create=bool(
            request_type is not None and has_permission(user, f"{prefix}.create")
        ),
        has_process=bool(
            request_type is not None and has_permission(user, f"{prefix}.process")
        ),
        has_manage=bool(has_permission(user, MANAGE_PERMISSION)),
        has_view_all=bool(has_permission(user, VIEW_ALL_PERMISSION)),
        branch_codes=branch_codes_for(user),
    )


def module_actor(user) -> Actor:
    """Actor sem tipo (listagens / admin de tipos)."""
    return Actor(
        user_id=_user_id(user),
        user_name=_user_name(user),
        has_access=bool(
            has_permission(user, ACCESS_PERMISSION)
            or has_permission(user, VIEW_ALL_PERMISSION)
            or has_permission(user, MANAGE_PERMISSION)
        ),
        has_create=False,
        has_process=False,
        has_manage=bool(has_permission(user, MANAGE_PERMISSION)),
        has_view_all=bool(has_permission(user, VIEW_ALL_PERMISSION)),
        branch_codes=branch_codes_for(user),
    )


def has_branch_access(actor: Actor, branch: str | None) -> bool:
    code = (branch or "").strip()
    if not code:
        return True
    if actor.has_manage or actor.has_view_all or actor.has_process:
        return True
    return code in actor.branch_codes
