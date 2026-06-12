"""Códigos RBAC do módulo Manutenção."""

from __future__ import annotations

import re
from typing import Any

from delpi_auth.authz_core import has_permission

MAINTENANCE_VIEW = "maintenance.view"
MAINTENANCE_MANAGE = "maintenance.manage"

MINI_APPLICATORS_VIEW_PREFIX = "maintenance.mini-applicators.view"
MINI_APPLICATORS_MANAGE_PREFIX = "maintenance.mini-applicators.manage"
MANUTENCAO_GERAL_VIEW_PREFIX = "maintenance.manutencao-geral.view"

_FILIAL_CODE_SUFFIX = re.compile(r"^[0-9]{2}$")
_SUBMODULE_VIEW_FILIAL_MARKER = ".view.filial-"
_SUBMODULE_MANAGE_FILIAL_MARKER = ".manage.filial-"

SUBMODULE_VIEW_PREFIXES: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_VIEW_PREFIX,
    "manutencao-geral": MANUTENCAO_GERAL_VIEW_PREFIX,
}

SUBMODULE_MANAGE_PREFIXES: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_MANAGE_PREFIX,
}


def submodule_view_permission(submodule_id: str, codigo_filial: str) -> str:
    base = SUBMODULE_VIEW_PREFIXES[submodule_id]
    return f"{base}.filial-{codigo_filial}"


def submodule_manage_permission(submodule_id: str, codigo_filial: str) -> str:
    base = SUBMODULE_MANAGE_PREFIXES[submodule_id]
    return f"{base}.filial-{codigo_filial}"


def codigos_from_submodule_filial_permissions(
    permissions: list[str],
    *,
    marker: str,
) -> list[str]:
    codigos: list[str] = []
    for permission in permissions:
        if not permission.startswith("maintenance.") or marker not in permission:
            continue
        codigo = permission.rsplit(marker, maxsplit=1)[-1]
        if _FILIAL_CODE_SUFFIX.match(codigo):
            codigos.append(codigo)
    return codigos


def can_manage_module(user: Any | None) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    return has_permission(user, MAINTENANCE_MANAGE)


def assert_module_manage(user: Any | None) -> None:
    if not can_manage_module(user):
        raise PermissionError("Sem permissão para gerenciar filiais do módulo.")
