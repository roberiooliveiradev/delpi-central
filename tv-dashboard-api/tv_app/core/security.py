from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any, Mapping

from delpi_auth.authz_core import has_permission
from fastapi import Request

TV_READ = "tv-dashboard.read"
TV_WRITE = "tv-dashboard.write"
TV_MANAGE = "tv-dashboard.manage"
TV_TEMPLATES_MANAGE = "tv-dashboard.templates.manage"
TV_ADMIN = "tv-dashboard.admin"


def _is_superadmin(user: Any | None) -> bool:
    return bool(user is not None and getattr(user, "is_superadmin", False))


def can(user: Any | None, permission: str) -> bool:
    if user is None:
        return False
    if _is_superadmin(user):
        return True
    if has_permission(user, TV_ADMIN):
        return True
    return has_permission(user, permission)


def assert_permission(user: Any | None, permission: str) -> None:
    if not can(user, permission):
        raise PermissionError("Você não tem permissão para esta ação.")


def actor_sub_from_request(request: Request) -> str | None:
    """Id do usuário autenticado (`user.id` do delpi_auth)."""
    user = getattr(request.state, "user", None)
    if user is None:
        return None
    for attr in ("id", "sub", "preferred_username"):
        raw = getattr(user, attr, None)
        if raw is None:
            continue
        value = str(raw).strip()
        if value:
            return value
    return None


class GovernedWriteAuthzError(Exception):
    """Fail-closed authorization error for governed material writes."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "AUTHZ_DENIED",
        status_code: int = 403,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


async def _fetch_fresh_rbac(token: str) -> dict:
    """Shared fail-closed fresh-RBAC primitive: no cache, no stale fallback."""
    from delpi_auth.middleware.fastapi_auth import load_user_rbac

    return await load_user_rbac(token, force_refresh=True)


def _bearer_token_for_write_authz(user: Any, authorization: str | None) -> str:
    token = str(getattr(user, "access_token", None) or "").strip()
    if token:
        return token
    scheme, _, raw = str(authorization or "").partition(" ")
    if scheme.lower() == "bearer" and raw.strip():
        return raw.strip()
    return ""


def _require_human_principal(user: Any) -> Any:
    if user is None:
        raise GovernedWriteAuthzError(
            "Autenticação necessária.",
            code="UNAUTHENTICATED",
            status_code=401,
        )
    if getattr(user, "principal_type", None) != "user":
        raise GovernedWriteAuthzError(
            "Escrita governada exige principal de usuário final.",
            code="PRINCIPAL_TYPE_DENIED",
            status_code=403,
        )
    return user


def _require_write_bearer(user: Any, authorization: str | None) -> str:
    token = _bearer_token_for_write_authz(user, authorization)
    if not token:
        raise GovernedWriteAuthzError(
            "Credencial do usuário indisponível para autorização fresh.",
            code="UNAUTHENTICATED",
            status_code=401,
        )
    return token


def _fresh_principal_from_rbac(user: Any, rbac: Mapping[str, Any]) -> Any:
    fields = dict(vars(user)) if hasattr(user, "__dict__") else {}
    for key in (
        "id",
        "email",
        "name",
        "roles",
        "groups",
        "permissions",
        "is_superadmin",
        "rbac_unavailable",
        "principal_type",
    ):
        fields.pop(key, None)
    return SimpleNamespace(
        **fields,
        id=rbac.get("id") or getattr(user, "id", None),
        email=rbac.get("email") or getattr(user, "email", None),
        name=rbac.get("name") or getattr(user, "name", None),
        roles=rbac.get("roles") or [],
        groups=rbac.get("groups") or [],
        permissions=list(rbac.get("permissions") or []),
        is_superadmin=bool(rbac.get("is_superadmin", False)),
        rbac_unavailable=False,
        principal_type="user",
    )


def _assert_fresh_permission(fresh_user: Any, permission: str) -> Any:
    try:
        assert_permission(fresh_user, permission)
    except PermissionError as exc:
        raise GovernedWriteAuthzError(
            str(exc), code="PERMISSION_DENIED", status_code=403
        ) from exc
    return fresh_user


def require_fresh_write_authorization(
    user: Any,
    *,
    authorization: str | None = None,
    permission: str = TV_WRITE,
) -> Any:
    """Gate for human-governed material writes (sync call sites).

    Order: ``principal_type == "user"`` → bearer credential → fresh effective
    RBAC from Core (``load_user_rbac(force_refresh=True)``: no cache, no stale
    fallback, fail-closed) → permission. Returns the freshly-authorized
    principal; callers must use it for resource AuthZ and the write itself.

    Internal S2S surfaces are explicit exceptions and never reach this gate.
    """
    _require_human_principal(user)
    token = _require_write_bearer(user, authorization)
    try:
        rbac = asyncio.run(_fetch_fresh_rbac(token))
    except GovernedWriteAuthzError:
        raise
    except Exception as exc:
        raise GovernedWriteAuthzError(
            "Serviço de autorização indisponível.",
            code="AUTHZ_UNAVAILABLE",
            status_code=503,
        ) from exc
    return _assert_fresh_permission(_fresh_principal_from_rbac(user, rbac), permission)


async def arequire_fresh_write_authorization(
    user: Any,
    *,
    authorization: str | None = None,
    permission: str = TV_WRITE,
) -> Any:
    """Async twin of ``require_fresh_write_authorization`` for async handlers."""
    _require_human_principal(user)
    token = _require_write_bearer(user, authorization)
    try:
        rbac = await _fetch_fresh_rbac(token)
    except GovernedWriteAuthzError:
        raise
    except Exception as exc:
        raise GovernedWriteAuthzError(
            "Serviço de autorização indisponível.",
            code="AUTHZ_UNAVAILABLE",
            status_code=503,
        ) from exc
    return _assert_fresh_permission(_fresh_principal_from_rbac(user, rbac), permission)
