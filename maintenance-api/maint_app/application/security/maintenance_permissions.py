"""Códigos RBAC do módulo Manutenção."""

from __future__ import annotations

MAINTENANCE_VIEW = "maintenance.view"

MINI_APPLICATORS_VIEW = "maintenance.mini-applicators.view"
MINI_APPLICATORS_MANAGE = "maintenance.mini-applicators.manage"

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

SUBMODULE_VIEW_PERMISSIONS: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_VIEW,
}

SUBMODULE_MANAGE_PERMISSIONS: dict[str, str] = {
    "mini-aplicadores": MINI_APPLICATORS_MANAGE,
}

BRANCH_VIEW_PERMISSIONS: tuple[str, ...] = tuple(VIEW_FILIAL_PERMISSIONS.values())
BRANCH_MANAGE_PERMISSIONS: tuple[str, ...] = tuple(MANAGE_FILIAL_PERMISSIONS.values())
