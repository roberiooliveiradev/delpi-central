"""Autorização do Portal de TI — backend-first, fail-closed.

- somente principal humano (`principal_type == "user"`); service tokens não
  operam o inventário;
- Core é a authority das permissões efetivas (`has_permission`); JWT válido
  sem a permissão não basta;
- `rbac_unavailable` (Core fora) falha fechado com 503;
- toda rota de dados exige `it-portal.access` + a permissão específica;
- toda escrita (`authorize_write`) revalida a permissão efetiva no Core sem
  cache nem fallback stale: permissão revogada não grava e Core fora → 503.
"""

from __future__ import annotations

import logging
import uuid
from types import SimpleNamespace

import anyio
from fastapi import Request

import delpi_auth.middleware.fastapi_auth as fastapi_auth
from delpi_auth.authz_core import has_permission

from it_portal_app.application.ports import Actor

logger = logging.getLogger(__name__)

ACCESS = "it-portal.access"
SERVERS_VIEW = "it-portal.servers.view"
SERVERS_MANAGE = "it-portal.servers.manage"
NOTES_CREATE = "it-portal.notes.create"
ACTIONS_VIEW = "it-portal.actions.view"
ACTIONS_MANAGE = "it-portal.actions.manage"
SERVICES_VIEW = "it-portal.services.view"
SERVICES_MANAGE = "it-portal.services.manage"
DATABASES_VIEW = "it-portal.databases.view"
DATABASES_MANAGE = "it-portal.databases.manage"

ALL_PERMISSIONS = (
    ACCESS,
    SERVERS_VIEW,
    SERVERS_MANAGE,
    NOTES_CREATE,
    ACTIONS_VIEW,
    ACTIONS_MANAGE,
    SERVICES_VIEW,
    SERVICES_MANAGE,
    DATABASES_VIEW,
    DATABASES_MANAGE,
)


def _human_user(request: Request):
    user = getattr(request.state, "user", None)
    if user is None:
        raise Exception("Unauthorized")
    if getattr(user, "principal_type", None) != "user":
        raise Exception("Forbidden")
    if getattr(user, "rbac_unavailable", False):
        raise Exception("Service Unavailable")
    return user


def authorize(request: Request, *permissions: str):
    """Usuário humano com `it-portal.access` e todas as `permissions` efetivas."""
    user = _human_user(request)
    for permission in (ACCESS, *permissions):
        if not has_permission(user, permission):
            raise Exception("Forbidden")
    return user


async def _fresh_rbac(token: str) -> dict:
    return await fastapi_auth.load_user_rbac(token, force_refresh=True)


def authorize_write(request: Request, *permissions: str):
    """`authorize` + revalidação fresh no Core para escritas materiais.

    Deve rodar em rota síncrona (worker thread do AnyIO): o lookup é delegado
    ao event loop da aplicação porque `load_user_rbac` serializa por um
    `asyncio.Lock` ligado ao loop. Retorna o principal fresh, que deve ser o
    autor da escrita.
    """
    user = authorize(request, *permissions)
    token = str(getattr(user, "access_token", None) or "").strip()
    if not token:
        raise Exception("Unauthorized")
    try:
        rbac = anyio.from_thread.run(_fresh_rbac, token)
    except Exception as exc:
        logger.error(
            "it_portal_write_authz_unavailable dependency=core_rbac error_class=%s",
            type(exc).__name__,
        )
        raise Exception("Service Unavailable") from None
    fresh = SimpleNamespace(
        **{
            **vars(user),
            "id": rbac.get("id") or getattr(user, "id", None),
            "name": rbac.get("name") or getattr(user, "name", None),
            "permissions": list(rbac.get("permissions") or []),
            "is_superadmin": bool(rbac.get("is_superadmin", False)),
            "rbac_unavailable": False,
        }
    )
    for permission in (ACCESS, *permissions):
        if not has_permission(fresh, permission):
            raise Exception("Forbidden")
    return fresh


def user_has(user, permission: str) -> bool:
    return has_permission(user, permission)


def actor_from(user) -> Actor:
    """Autor real para auditoria: subject UUID resolvido pelo Core, sem fallback."""
    try:
        actor_id = str(uuid.UUID(str(getattr(user, "id", None))))
    except (TypeError, ValueError):
        raise Exception("Unauthorized") from None
    name = (getattr(user, "name", None) or "").strip()[:200] or "Usuário"
    return Actor(id=actor_id, name=name)
