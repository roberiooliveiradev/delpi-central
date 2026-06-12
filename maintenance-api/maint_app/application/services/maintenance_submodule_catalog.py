from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

from maint_app.application.security.maintenance_permissions import (
    SUBMODULE_MANAGE_PERMISSIONS,
    SUBMODULE_VIEW_PERMISSIONS,
    submodule_view_permission,
)
from maint_app.application.services.filial_access_scope_service import (
    FilialAccessScope,
    FilialAccessScopeService,
)

_scope_service = FilialAccessScopeService()

SUBMODULE_CATALOG: tuple[dict[str, Any], ...] = (
    {
        "id": "mini-aplicadores",
        "label": "Mini-aplicadores",
        "description": "Reposição de peças, golpes e alertas preventivos.",
        "icon": "hammer",
        "entry_path": "/apps/maintenance/mini-aplicadores",
        "view_permission": SUBMODULE_VIEW_PERMISSIONS["mini-aplicadores"],
        "manage_permission": SUBMODULE_MANAGE_PERMISSIONS["mini-aplicadores"],
        "filiais": None,
    },
    {
        "id": "manutencao-geral",
        "label": "Manutenção geral",
        "description": "Registro de máquinas, equipamentos, lâmpadas e demais ocorrências.",
        "icon": "clipboard-list",
        "entry_path": "/apps/maintenance/filial-01/manutencao-geral",
        "view_permission": SUBMODULE_VIEW_PERMISSIONS["manutencao-geral"],
        "manage_permission": None,
        "filiais": ("01",),
    },
)


def _normalize_filial(codigo: str | None) -> str | None:
    if codigo is None:
        return None
    value = str(codigo).strip()
    return value or None


def _get_submodule(submodule_id: str) -> dict[str, Any] | None:
    for submodule in SUBMODULE_CATALOG:
        if submodule["id"] == submodule_id:
            return submodule
    return None


def _submodule_filiais(submodule: dict[str, Any]) -> frozenset[str] | None:
    raw = submodule.get("filiais")
    if not raw:
        return None
    return frozenset(_normalize_filial(item) for item in raw if _normalize_filial(item))


def _scope_allows_filial(scope: FilialAccessScope | None, codigo_filial: str) -> bool:
    if scope is None:
        return True
    return _scope_service.can_view_filial(scope, codigo_filial)


def _has_filial_submodule_view(
    user: Any,
    submodule_id: str,
    codigo_filial: str,
    *,
    scope: FilialAccessScope | None,
) -> bool:
    codigo = _normalize_filial(codigo_filial)
    if not codigo:
        return False

    filial_permission = submodule_view_permission(submodule_id, codigo)
    if not has_permission(user, filial_permission):
        return False
    return _scope_allows_filial(scope, codigo)


def _can_view_submodule(
    user: Any | None,
    submodule_id: str,
    *,
    codigo_filial: str | None = None,
    scope: FilialAccessScope | None = None,
) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True

    submodule = _get_submodule(submodule_id)
    if submodule is None:
        return False

    filiais = _submodule_filiais(submodule)
    if filiais is None:
        permission = SUBMODULE_VIEW_PERMISSIONS.get(submodule_id)
        return bool(permission and has_permission(user, permission))

    if codigo_filial:
        codigo = _normalize_filial(codigo_filial)
        if not codigo or codigo not in filiais:
            return False
        return _has_filial_submodule_view(user, submodule_id, codigo, scope=scope)

    return any(
        _has_filial_submodule_view(user, submodule_id, codigo, scope=scope)
        for codigo in sorted(filiais)
    )


def _submodule_available_for_filial(submodule: dict[str, Any], codigo_filial: str | None) -> bool:
    filiais = _submodule_filiais(submodule)
    if filiais is None:
        return True
    codigo = _normalize_filial(codigo_filial)
    if not codigo:
        return True
    return codigo in filiais


def _can_manage_submodule(user: Any | None, submodule_id: str) -> bool:
    if user is None:
        return False
    if getattr(user, "is_superadmin", False):
        return True
    permission = SUBMODULE_MANAGE_PERMISSIONS.get(submodule_id)
    return bool(permission and has_permission(user, permission))


def _serialize_submodule(
    submodule: dict[str, Any],
    *,
    user: Any | None,
) -> dict[str, Any]:
    manage_permission = submodule.get("manage_permission")
    can_manage = False
    if manage_permission:
        can_manage = _can_manage_submodule(user, submodule["id"])

    filiais = _submodule_filiais(submodule)
    return {
        "id": submodule["id"],
        "label": submodule["label"],
        "description": submodule["description"],
        "icon": submodule["icon"],
        "entry_path": submodule["entry_path"],
        "can_manage": can_manage,
        "filiais": sorted(filiais) if filiais else None,
    }


def filter_submodules_for_user(
    user: Any | None,
    *,
    filial: str | None = None,
    scope: FilialAccessScope | None = None,
) -> list[dict[str, Any]]:
    codigo_filial = _normalize_filial(filial)
    result: list[dict[str, Any]] = []

    for submodule in SUBMODULE_CATALOG:
        if not _submodule_available_for_filial(submodule, codigo_filial):
            continue
        if codigo_filial and scope is not None and not _scope_allows_filial(scope, codigo_filial):
            continue
        if not _can_view_submodule(
            user,
            submodule["id"],
            codigo_filial=codigo_filial,
            scope=scope,
        ):
            continue
        result.append(_serialize_submodule(submodule, user=user))

    return result


def assert_submodule_view(
    user: Any | None,
    submodule_id: str,
    *,
    codigo_filial: str | None = None,
    scope: FilialAccessScope | None = None,
) -> None:
    if not _can_view_submodule(
        user,
        submodule_id,
        codigo_filial=codigo_filial,
        scope=scope,
    ):
        raise PermissionError("Sem permissão para acessar este submódulo.")


def assert_submodule_manage(user: Any | None, submodule_id: str) -> None:
    if not _can_manage_submodule(user, submodule_id):
        raise PermissionError("Sem permissão para alterar dados deste submódulo.")
