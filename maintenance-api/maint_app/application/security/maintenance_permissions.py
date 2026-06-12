"""Códigos RBAC do módulo Manutenção — alinhados a maintenance.manifest.json."""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

MAINTENANCE_VIEW = "maintenance.view"
MAINTENANCE_MANAGE = "maintenance.manage"

MINI_APPLICATORS_VIEW_PREFIX = "maintenance.mini-applicators.view"
MINI_APPLICATORS_MANAGE_PREFIX = "maintenance.mini-applicators.manage"
MANUTENCAO_GERAL_VIEW_PREFIX = "maintenance.manutencao-geral.view"

# Manifest v0.2.1 — mapa explícito filial → permissão (não usar marcadores genéricos).
MINI_APPLICATORS_VIEW_FILIAL: dict[str, str] = {
    "01": "maintenance.mini-applicators.view.filial-01",
    "02": "maintenance.mini-applicators.view.filial-02",
}

MINI_APPLICATORS_MANAGE_FILIAL: dict[str, str] = {
    "01": "maintenance.mini-applicators.manage.filial-01",
    "02": "maintenance.mini-applicators.manage.filial-02",
}

MANUTENCAO_GERAL_VIEW_FILIAL: dict[str, str] = {
    "01": "maintenance.manutencao-geral.view.filial-01",
}

SUBMODULE_VIEW_PREFIXES: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_VIEW_PREFIX,
    "manutencao-geral": MANUTENCAO_GERAL_VIEW_PREFIX,
}

SUBMODULE_MANAGE_PREFIXES: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_MANAGE_PREFIX,
}

VIEW_FILIAL_PERMISSIONS: tuple[str, ...] = tuple(
    dict.fromkeys(
        [
            *MINI_APPLICATORS_VIEW_FILIAL.values(),
            *MANUTENCAO_GERAL_VIEW_FILIAL.values(),
        ]
    )
)

MANAGE_FILIAL_PERMISSIONS: tuple[str, ...] = tuple(MINI_APPLICATORS_MANAGE_FILIAL.values())


def filial_codes_from_permission_map(
    permissions: list[str],
    mapping: dict[str, str],
) -> list[str]:
    return sorted(codigo for codigo, perm in mapping.items() if perm in permissions)


def view_filial_codes_from_permissions(permissions: list[str]) -> list[str]:
    """Filials com leitura — união dos submódulos declarados no manifesto."""
    codigos: set[str] = set()
    codigos.update(
        filial_codes_from_permission_map(permissions, MINI_APPLICATORS_VIEW_FILIAL),
    )
    codigos.update(
        filial_codes_from_permission_map(permissions, MANUTENCAO_GERAL_VIEW_FILIAL),
    )
    return sorted(codigos)


def manage_filial_codes_from_permissions(permissions: list[str]) -> list[str]:
    """Filials com escrita operacional (mini-aplicadores) — manifesto."""
    return filial_codes_from_permission_map(permissions, MINI_APPLICATORS_MANAGE_FILIAL)


def submodule_view_permission(submodule_id: str, codigo_filial: str) -> str:
    base = SUBMODULE_VIEW_PREFIXES[submodule_id]
    return f"{base}.filial-{codigo_filial}"


def submodule_manage_permission(submodule_id: str, codigo_filial: str) -> str:
    base = SUBMODULE_MANAGE_PREFIXES[submodule_id]
    return f"{base}.filial-{codigo_filial}"


def can_manage_module(user: Any | None) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    return has_permission(user, MAINTENANCE_MANAGE)


def assert_module_manage(user: Any | None) -> None:
    if not can_manage_module(user):
        raise PermissionError("Sem permissão para gerenciar filiais do módulo.")
