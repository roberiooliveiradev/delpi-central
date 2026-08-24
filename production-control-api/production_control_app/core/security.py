"""Códigos RBAC do Portal PCP — alinhados a production-control.manifest.json."""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

PC_ACCESS = "production-control.access"
PC_PROBLEM_ANALYSIS_VIEW = "production-control.problem-analysis.view"
PC_MACHINE_LOAD_VIEW = "production-control.machine-load.view"
PC_DEMAND_VIEW = "production-control.demand.view"
PC_MATERIALS_VIEW = "production-control.materials.view"
PC_DELIVERY_MAP_VIEW = "production-control.delivery-map.view"
PC_VIEW_FILIAL_01 = "production-control.view.filial-01"
PC_VIEW_FILIAL_02 = "production-control.view.filial-02"

BRANCH_VIEW_PERMISSIONS: dict[str, str] = {
    "01": PC_VIEW_FILIAL_01,
    "02": PC_VIEW_FILIAL_02,
}

ALLOWED_BRANCHES: frozenset[str] = frozenset(BRANCH_VIEW_PERMISSIONS)


def _is_superadmin(user: Any | None) -> bool:
    return bool(user is not None and getattr(user, "is_superadmin", False))


def can(user: Any | None, permission: str) -> bool:
    if user is None:
        return False
    if _is_superadmin(user):
        return True
    return has_permission(user, permission)
