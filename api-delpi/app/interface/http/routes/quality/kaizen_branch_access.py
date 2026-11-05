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


def writable_branch_codes() -> set[str]:
    """Unidades que o usuário pode alterar (write scope — JWT branch-*)."""
    return allowed_branch_codes()


def branch_view_allowed(branch: str) -> bool:
    """Escopo de ESCRITA: usuário só altera kaizens das próprias unidades."""
    code = str(branch or "").strip()
    if code not in _ALL_BRANCHES:
        return False
    return code in allowed_branch_codes()


def branch_read_allowed(branch: str) -> bool:
    """Escopo de LEITURA: qualquer unidade conhecida do Kaizômetro."""
    code = str(branch or "").strip()
    return code in _ALL_BRANCHES


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


def branch_write_error(branch: str):
    """Gate de ESCRITA: usuário só altera kaizens das próprias unidades."""
    return branch_access_error(branch)


def resolve_query_branch(branch: str | None) -> tuple[str | None, object | None]:
    """Resolve filtro de listagem/summary (escopo de LEITURA).

    Returns:
        (branch_efetivo, erro_http). ``branch_efetivo`` None = todas as
        unidades — leitura é permitida em qualquer filial; a restrição
        RBAC por ``branch-*`` vale apenas para escrita.
    """
    requested = (branch or "").strip() or None
    if requested:
        if not branch_read_allowed(requested):
            return None, error_response(
                "Unidade desconhecida para o Kaizômetro.",
                status_code=422,
                code="INVALID_BRANCH",
                recoverable=False,
            )
        return requested, None

    return None, None
