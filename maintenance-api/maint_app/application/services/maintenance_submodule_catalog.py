from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

from maint_app.application.security.maintenance_permissions import (
    SUBMODULE_MANAGE_PERMISSIONS,
    SUBMODULE_VIEW_PERMISSIONS,
)

SUBMODULE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "mini-aplicadores",
        "label": "Mini-aplicadores",
        "description": "Reposição de peças, golpes e alertas preventivos.",
        "icon": "hammer",
        "entry_path": "/apps/maintenance/mini-aplicadores",
        "view_permission": SUBMODULE_VIEW_PERMISSIONS["mini-aplicadores"],
        "manage_permission": SUBMODULE_MANAGE_PERMISSIONS["mini-aplicadores"],
    },
    {
        "id": "manutencao-geral",
        "label": "Manutenção geral",
        "description": "Registro de máquinas, equipamentos, lâmpadas e demais ocorrências.",
        "icon": "clipboard-list",
        "entry_path": "/apps/maintenance/manutencao-geral",
        "view_permission": SUBMODULE_VIEW_PERMISSIONS["manutencao-geral"],
        "manage_permission": None,
    },
)


def _can_view_submodule(user: Any | None, submodule_id: str) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    permission = SUBMODULE_VIEW_PERMISSIONS.get(submodule_id)
    return bool(permission and has_permission(user, permission))


def _can_manage_submodule(user: Any | None, submodule_id: str) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    permission = SUBMODULE_MANAGE_PERMISSIONS.get(submodule_id)
    return bool(permission and has_permission(user, permission))


def filter_submodules_for_user(user: Any | None) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for submodule in SUBMODULE_CATALOG:
        if not _can_view_submodule(user, submodule["id"]):
            continue
        manage_permission = submodule.get("manage_permission")
        can_manage = False
        if manage_permission:
            can_manage = _can_manage_submodule(user, submodule["id"])
        result.append(
            {
                "id": submodule["id"],
                "label": submodule["label"],
                "description": submodule["description"],
                "icon": submodule["icon"],
                "entry_path": submodule["entry_path"],
                "can_manage": can_manage,
            }
        )
    return result


def assert_submodule_view(user: Any | None, submodule_id: str) -> None:
    if not _can_view_submodule(user, submodule_id):
        raise PermissionError("Sem permissão para acessar este submódulo.")


def assert_submodule_manage(user: Any | None, submodule_id: str) -> None:
    if not _can_manage_submodule(user, submodule_id):
        raise PermissionError("Sem permissão para alterar dados deste submódulo.")
