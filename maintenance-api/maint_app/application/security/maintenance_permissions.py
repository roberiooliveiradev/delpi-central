"""Códigos RBAC do módulo Manutenção — escopo por filial."""

from __future__ import annotations

MAINTENANCE_VIEW = "maintenance.view"
MAINTENANCE_REPLACEMENTS_MANAGE = "maintenance.replacements.manage"
MAINTENANCE_REASONS_MANAGE = "maintenance.reasons.manage"
MAINTENANCE_STATUS_MANAGE = "maintenance.status.manage"
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

GLOBAL_MANAGE_PERMISSIONS: tuple[str, ...] = (
    MAINTENANCE_REPLACEMENTS_MANAGE,
    MAINTENANCE_REASONS_MANAGE,
    MAINTENANCE_STATUS_MANAGE,
)

BRANCH_VIEW_PERMISSIONS: tuple[str, ...] = tuple(VIEW_FILIAL_PERMISSIONS.values())
BRANCH_MANAGE_PERMISSIONS: tuple[str, ...] = tuple(MANAGE_FILIAL_PERMISSIONS.values())
