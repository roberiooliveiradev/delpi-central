"""Códigos RBAC do Transformômetro — escopo por filial (Playbook 18 S10)."""

from __future__ import annotations

TRANSFORMOMETRO_VIEW = "transformometro.view"
TRANSFORMOMETRO_VIEW_CONSOLIDATED = "transformometro.view.consolidated"
TRANSFORMOMETRO_VIEW_FILIAL_01 = "transformometro.view.filial-01"
TRANSFORMOMETRO_VIEW_FILIAL_02 = "transformometro.view.filial-02"
TRANSFORMOMETRO_MANAGE_FILIAL_01 = "transformometro.manage.filial-01"
TRANSFORMOMETRO_MANAGE_FILIAL_02 = "transformometro.manage.filial-02"

TRANSFORMOMETRO_PROCESSES_MANAGE = "transformometro.processes.manage"
TRANSFORMOMETRO_REVISIONS_MANAGE = "transformometro.revisions.manage"
TRANSFORMOMETRO_MEASUREMENTS_MANAGE = "transformometro.measurements.manage"
TRANSFORMOMETRO_INVESTMENTS_MANAGE = "transformometro.investments.manage"
TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE = "transformometro.shared-resources.manage"

VIEW_FILIAL_PERMISSIONS: dict[str, str] = {
    "01": TRANSFORMOMETRO_VIEW_FILIAL_01,
    "02": TRANSFORMOMETRO_VIEW_FILIAL_02,
}

MANAGE_FILIAL_PERMISSIONS: dict[str, str] = {
    "01": TRANSFORMOMETRO_MANAGE_FILIAL_01,
    "02": TRANSFORMOMETRO_MANAGE_FILIAL_02,
}

GLOBAL_MANAGE_PERMISSIONS: tuple[str, ...] = (
    TRANSFORMOMETRO_PROCESSES_MANAGE,
    TRANSFORMOMETRO_REVISIONS_MANAGE,
    TRANSFORMOMETRO_MEASUREMENTS_MANAGE,
    TRANSFORMOMETRO_INVESTMENTS_MANAGE,
    TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE,
)

BRANCH_VIEW_PERMISSIONS: tuple[str, ...] = tuple(VIEW_FILIAL_PERMISSIONS.values())
BRANCH_MANAGE_PERMISSIONS: tuple[str, ...] = tuple(MANAGE_FILIAL_PERMISSIONS.values())
