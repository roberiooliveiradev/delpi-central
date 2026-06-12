"""Códigos RBAC do módulo Manutenção."""

from __future__ import annotations

import re

MAINTENANCE_VIEW = "maintenance.view"

MINI_APPLICATORS_VIEW = "maintenance.mini-applicators.view"
MINI_APPLICATORS_MANAGE = "maintenance.mini-applicators.manage"

MANUTENCAO_GERAL_VIEW = "maintenance.manutencao-geral.view"

VIEW_FILIAL_PREFIX = "maintenance.view.filial-"
MANAGE_FILIAL_PREFIX = "maintenance.manage.filial-"
_FILIAL_CODE_SUFFIX = re.compile(r"^[0-9]{2}$")

MAINTENANCE_VIEW_FILIAL_01 = "maintenance.view.filial-01"
MAINTENANCE_VIEW_FILIAL_02 = "maintenance.view.filial-02"
MAINTENANCE_MANAGE_FILIAL_01 = "maintenance.manage.filial-01"
MAINTENANCE_MANAGE_FILIAL_02 = "maintenance.manage.filial-02"

VIEW_FILIAL_PERMISSIONS: dict[str, str] = {
    "01": MAINTENANCE_VIEW_FILIAL_01,
    "02": MAINTENANCE_VIEW_FILIAL_02,
}

MANAGE_FILIAL_PERMISSIONS: dict[str, str] = {
    "01": MAINTENANCE_MANAGE_FILIAL_01,
    "02": MAINTENANCE_MANAGE_FILIAL_02,
}


def view_filial_permission(codigo_filial: str) -> str:
    return f"{VIEW_FILIAL_PREFIX}{codigo_filial}"


def manage_filial_permission(codigo_filial: str) -> str:
    return f"{MANAGE_FILIAL_PREFIX}{codigo_filial}"


def codigos_from_filial_permissions(
    permissions: list[str],
    *,
    prefix: str,
) -> list[str]:
    codigos: list[str] = []
    for permission in permissions:
        if not permission.startswith(prefix):
            continue
        codigo = permission[len(prefix) :]
        if _FILIAL_CODE_SUFFIX.match(codigo):
            codigos.append(codigo)
    return codigos


SUBMODULE_VIEW_PERMISSIONS: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_VIEW,
    "manutencao-geral": MANUTENCAO_GERAL_VIEW,
}

SUBMODULE_MANAGE_PERMISSIONS: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_MANAGE,
}

BRANCH_VIEW_PERMISSIONS: tuple[str, ...] = tuple(VIEW_FILIAL_PERMISSIONS.values())
BRANCH_MANAGE_PERMISSIONS: tuple[str, ...] = tuple(MANAGE_FILIAL_PERMISSIONS.values())
