from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

MES_ACCESS = "delpi-mes.access"
MES_MONITORING_VIEW = "delpi-mes.monitoring.view"
MES_DOWNTIMES_VIEW = "delpi-mes.downtimes.view"
MES_HISTORY_VIEW = "delpi-mes.history.view"
BRANCH_VIEW_PERMISSIONS = {
    "01": "delpi-mes.view.filial-01",
    "02": "delpi-mes.view.filial-02",
}


def is_human_user(user: Any | None) -> bool:
    return user is not None and getattr(user, "principal_type", None) == "user"


def can(user: Any | None, permission: str) -> bool:
    if not is_human_user(user):
        return False
    if getattr(user, "is_superadmin", False):
        return True
    return has_permission(user, permission)
