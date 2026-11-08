"""Autenticação operacional da prévia — reusa delpi_auth (JWT + RBAC Core).

Não aceita identidade sintética nem ``is_superadmin`` informado pelo operador.
O token deve vir de variável de ambiente (nunca impresso).
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from typing import Any

from delpi_auth.jwt_validator import validate_token
from delpi_auth.middleware.fastapi_auth import load_user_rbac
from delpi_auth.request_context import (
    reset_request_authorization,
    set_request_authorization,
)


class PreviewAuthError(RuntimeError):
    """Falha de autenticação/autorização da prévia operacional."""


def resolve_access_token(*, env_var: str = "ACCESS_TOKEN") -> str:
    """Lê Bearer JWT de env. Não loga o valor."""
    name = (env_var or "ACCESS_TOKEN").strip() or "ACCESS_TOKEN"
    token = (os.environ.get(name) or "").strip()
    if not token:
        raise PreviewAuthError(
            f"Variável {name} ausente. A prévia operacional exige JWT de usuário "
            "real (mesmo fluxo do Portal). Não use identidade sintética."
        )
    if token.lower().startswith("bearer "):
        token = token.split(" ", 1)[1].strip()
    if not token:
        raise PreviewAuthError(f"{name} vazia após remover prefixo Bearer.")
    return token


async def _load_user_from_token(token: str) -> Any:
    claims = validate_token(token)
    sub = claims.get("sub")
    email = claims.get("email")
    if not sub or not email:
        raise PreviewAuthError("JWT sem claims sub/email obrigatórios.")
    try:
        rbac = await load_user_rbac(token, force_refresh=True)
    except Exception as exc:  # noqa: BLE001
        # Sem Core RBAC, permissões do token ficam vazias — fail-closed para prévia.
        raise PreviewAuthError(
            "Não foi possível carregar RBAC em /me (Core). Prévia bloqueada."
        ) from exc
    name = rbac.get("name") or claims.get("name") or email or "Usuário"
    return SimpleNamespace(
        id=rbac.get("id") or sub,
        email=rbac.get("email") or email,
        name=name,
        roles=rbac.get("roles", []),
        groups=rbac.get("groups", []),
        permissions=rbac.get("permissions", []),
        is_superadmin=bool(rbac.get("is_superadmin", False)),
        rbac_unavailable=bool(rbac.get("rbac_unavailable")),
        access_token=token,
        principal_type="user",
    )


def authenticate_preview_user(*, env_var: str = "ACCESS_TOKEN") -> tuple[Any, Any]:
    """Valida JWT + RBAC e instala Authorization no contexto do gateway.

    Retorna ``(user, auth_context_token)`` — o caller deve ``reset`` no finally.
    """
    token = resolve_access_token(env_var=env_var)
    user = asyncio.run(_load_user_from_token(token))
    if getattr(user, "rbac_unavailable", False):
        raise PreviewAuthError("RBAC indisponível — prévia bloqueada (fail-closed).")
    # is_superadmin só vale se veio do Core /me, nunca de input do operador.
    auth_ctx = set_request_authorization(f"Bearer {token}")
    return user, auth_ctx


def release_preview_auth(auth_context_token: Any) -> None:
    reset_request_authorization(auth_context_token)


# Evita import * acidental do helper privado em outros módulos de produção.
__all__ = [
    "PreviewAuthError",
    "authenticate_preview_user",
    "release_preview_auth",
    "resolve_access_token",
]
