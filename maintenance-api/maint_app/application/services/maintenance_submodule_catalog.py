from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

from maint_app.application.security.maintenance_permissions import (
    SUBMODULE_MANAGE_PREFIXES,
    SUBMODULE_VIEW_PREFIXES,
    submodule_manage_permission,
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
        "filiais": None,
    },
    {
        "id": "manutencao-geral",
        "label": "Manutenção geral",
        "description": "Registro de máquinas, equipamentos, lâmpadas e demais ocorrências.",
        "icon": "clipboard-list",
        "entry_path": "/apps/maintenance/filial-01/manutencao-geral",
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


def _has_submodule_view_for_filial(
    user: Any,
    submodule_id: str,
    codigo_filial: str,
    *,
    scope: FilialAccessScope | None,
) -> bool:
    codigo = _normalize_filial(codigo_filial)
    if not codigo or submodule_id not in SUBMODULE_VIEW_PREFIXES:
        return False
    if not has_permission(user, submodule_view_permission(submodule_id, codigo)):
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
    candidate_filiais = sorted(filiais) if filiais else []

    if codigo_filial:
        codigo = _normalize_filial(codigo_filial)
        if not codigo:
            return False
        if filiais is not None and codigo not in filiais:
            return False
        return _has_submodule_view_for_filial(user, submodule_id, codigo, scope=scope)

    if candidate_filiais:
        return any(
            _has_submodule_view_for_filial(user, submodule_id, codigo, scope=scope)
            for codigo in candidate_filiais
        )

    if scope is not None and not scope.is_unrestricted:
        return any(
            _has_submodule_view_for_filial(user, submodule_id, codigo, scope=scope)
            for codigo in sorted(scope.allowed_codigos)
        )

    permissions = list(getattr(user, "permissions", []) or [])
    prefix = f"{SUBMODULE_VIEW_PREFIXES[submodule_id]}.filial-"
    return any(item.startswith(prefix) for item in permissions)


def _submodule_available_for_filial(submodule: dict[str, Any], codigo_filial: str | None) -> bool:
    filiais = _submodule_filiais(submodule)
    if filiais is None:
        return True
    codigo = _normalize_filial(codigo_filial)
    if not codigo:
        return True
    return codigo in filiais


def _can_manage_submodule(
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
    if submodule_id not in SUBMODULE_MANAGE_PREFIXES:
        return False

    codigo = _normalize_filial(codigo_filial)
    if not codigo:
        permissions = list(getattr(user, "permissions", []) or [])
        prefix = f"{SUBMODULE_MANAGE_PREFIXES[submodule_id]}.filial-"
        if any(item.startswith(prefix) for item in permissions):
            return True
        if scope is not None and scope.manage_codigos:
            return True
        return False

    if scope is not None:
        return _scope_service.can_manage_filial(
            scope,
            codigo,
            user=user,
            submodule_id=submodule_id,
        )

    return has_permission(user, submodule_manage_permission(submodule_id, codigo))


def _serialize_submodule(
    submodule: dict[str, Any],
    *,
    user: Any | None,
    codigo_filial: str | None = None,
    scope: FilialAccessScope | None = None,
) -> dict[str, Any]:
    filiais = _submodule_filiais(submodule)
    return {
        "id": submodule["id"],
        "label": submodule["label"],
        "description": submodule["description"],
        "icon": submodule["icon"],
        "entry_path": submodule["entry_path"],
        "can_manage": _can_manage_submodule(
            user,
            submodule["id"],
            codigo_filial=codigo_filial,
            scope=scope,
        ),
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
        result.append(
            _serialize_submodule(
                submodule,
                user=user,
                codigo_filial=codigo_filial,
                scope=scope,
            )
        )

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


def assert_submodule_manage(
    user: Any | None,
    submodule_id: str,
    *,
    codigo_filial: str | None = None,
    scope: FilialAccessScope | None = None,
) -> None:
    if not _can_manage_submodule(
        user,
        submodule_id,
        codigo_filial=codigo_filial,
        scope=scope,
    ):
        raise PermissionError("Sem permissão para alterar dados deste submódulo.")
