"""Autorização por unidade — Kaizômetro (`kaizometro.branch-01|02`)."""

from __future__ import annotations

from delpi_auth.authz_core import has_permission
from delpi_auth.request_context import get_current_user

from app.application.security.api_delpi_permissions import KAIZOMETRO_BRANCH_VIEW_PERMS
from app.core.responses import error_response

_ALL_BRANCHES = frozenset(KAIZOMETRO_BRANCH_VIEW_PERMS.keys())


def _is_superadmin() -> bool:
    user = get_current_user()
    return bool(user and getattr(user, "is_superadmin", False))


def allowed_branch_codes() -> set[str]:
    """Unidades que o usuário pode operar.

    Superadmin → ambas. Caso contrário só as chaves de
    ``KAIZOMETRO_BRANCH_VIEW_PERMS`` presentes no JWT.
    ``kaizometro.view`` sozinho **não** libera unidades.
    """
    if _is_superadmin():
        return set(_ALL_BRANCHES)

    user = get_current_user()
    if user is None:
        return set()

    allowed: set[str] = set()
    for code, perm in KAIZOMETRO_BRANCH_VIEW_PERMS.items():
        if has_permission(user, perm):
            allowed.add(code)
    return allowed


def branch_view_allowed(branch: str) -> bool:
    code = str(branch or "").strip()
    if code not in _ALL_BRANCHES:
        return False
    return code in allowed_branch_codes()


def branch_access_error(branch: str):
    if branch_view_allowed(branch):
        return None
    return error_response(
        "Sem permissão para acessar kaizens desta unidade.",
        status_code=403,
        code="BRANCH_FORBIDDEN",
        recoverable=False,
    )


def no_branch_scope_error():
    """Quando o usuário não tem nenhuma ``branch-*``."""
    return error_response(
        "Sem permissão de unidade (kaizometro.branch-01 ou branch-02).",
        status_code=403,
        code="BRANCH_SCOPE_REQUIRED",
        recoverable=False,
    )


def resolve_query_branch(branch: str | None) -> tuple[str | None, object | None]:
    """Resolve filtro de listagem/summary.

    Returns:
        (branch_efetivo, erro_http). ``branch_efetivo`` None = todas as
        unidades permitidas (usuário tem as duas).
    """
    allowed = allowed_branch_codes()
    if not allowed:
        return None, no_branch_scope_error()

    requested = (branch or "").strip() or None
    if requested:
        err = branch_access_error(requested)
        if err is not None:
            return None, err
        return requested, None

    if len(allowed) == 1:
        return next(iter(allowed)), None

    return None, None
