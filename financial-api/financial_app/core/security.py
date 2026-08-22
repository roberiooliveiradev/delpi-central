"""Códigos RBAC do Portal Financeiro — alinhados a financial.manifest.json."""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

FIN_ACCESS = "financial.access"
FIN_DELINQUENCY_VIEW = "financial.delinquency.view"
FIN_COST_CENTERS_VIEW = "financial.cost-centers.view"
FIN_INDICATORS_VIEW = "financial.indicators.view"
FIN_EXPORT = "financial.export"
FIN_VIEW_FILIAL_01 = "financial.view.filial-01"
FIN_VIEW_FILIAL_02 = "financial.view.filial-02"

BRANCH_VIEW_PERMISSIONS: dict[str, str] = {
    "01": FIN_VIEW_FILIAL_01,
    "02": FIN_VIEW_FILIAL_02,
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
