from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from delpi_auth.authz_core import has_any_permission, has_permission

from maint_app.application.security.maintenance_permissions import (
    BRANCH_MANAGE_PERMISSIONS,
    BRANCH_VIEW_PERMISSIONS,
    GLOBAL_MANAGE_PERMISSIONS,
    MAINTENANCE_VIEW,
    MANAGE_FILIAL_PERMISSIONS,
    VIEW_FILIAL_PERMISSIONS,
)


def _normalize_codigo(codigo: str | None) -> str | None:
    if codigo is None:
        return None
    value = str(codigo).strip()
    return value or None


@dataclass(frozen=True)
class FilialAccessScope:
    mode: str
    allowed_codigos: frozenset[str]
    scoped_manage: bool

    @property
    def is_unrestricted(self) -> bool:
        return self.mode == "unrestricted"

    def meta(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "allowed_filiais": sorted(self.allowed_codigos),
            "scoped_manage": self.scoped_manage,
        }


class FilialAccessScopeService:
    def resolve(self, user: Any | None) -> FilialAccessScope:
        if user is None or getattr(user, "is_superadmin", False):
            return FilialAccessScope(
                mode="unrestricted",
                allowed_codigos=frozenset(),
                scoped_manage=False,
            )

        permissions = list(getattr(user, "permissions", []) or [])
        branch_view = [
            codigo
            for codigo, perm in VIEW_FILIAL_PERMISSIONS.items()
            if perm in permissions
        ]
        branch_manage = [
            codigo
            for codigo, perm in MANAGE_FILIAL_PERMISSIONS.items()
            if perm in permissions
        ]

        if branch_view:
            return FilialAccessScope(
                mode="scoped",
                allowed_codigos=frozenset(branch_view),
                scoped_manage=bool(branch_manage),
            )

        if has_permission(user, MAINTENANCE_VIEW):
            return FilialAccessScope(
                mode="unrestricted",
                allowed_codigos=frozenset(),
                scoped_manage=bool(branch_manage),
            )

        return FilialAccessScope(
            mode="scoped",
            allowed_codigos=frozenset(),
            scoped_manage=False,
        )

    def can_view_filial(self, scope: FilialAccessScope, codigo_filial: str | None) -> bool:
        codigo = _normalize_codigo(codigo_filial)
        if not codigo:
            return False
        if scope.is_unrestricted:
            return True
        return codigo in scope.allowed_codigos

    def can_manage_filial(
        self,
        scope: FilialAccessScope,
        codigo_filial: str | None,
        *,
        user: Any | None,
    ) -> bool:
        codigo = _normalize_codigo(codigo_filial)
        if not codigo:
            return False
        if user is not None and getattr(user, "is_superadmin", False):
            return True

        permissions = list(getattr(user, "permissions", []) or []) if user else []
        manage_perm = MANAGE_FILIAL_PERMISSIONS.get(codigo)
        if manage_perm and manage_perm in permissions:
            return True

        if scope.is_unrestricted and not scope.scoped_manage:
            return has_any_permission(user, GLOBAL_MANAGE_PERMISSIONS) if user else False

        if has_any_permission(user, GLOBAL_MANAGE_PERMISSIONS):
            return True

        return False

    def filter_filiais_options(
        self,
        filiais: list[dict[str, Any]],
        scope: FilialAccessScope,
    ) -> list[dict[str, Any]]:
        if scope.is_unrestricted:
            return filiais
        allowed = scope.allowed_codigos
        return [item for item in filiais if _normalize_codigo(item.get("id")) in allowed]

    def assert_view_filial(self, scope: FilialAccessScope, codigo_filial: str) -> None:
        if not self.can_view_filial(scope, codigo_filial):
            raise PermissionError("Sem permissão para acessar esta filial.")

    def assert_manage_filial(
        self,
        scope: FilialAccessScope,
        codigo_filial: str,
        *,
        user: Any | None,
    ) -> None:
        if not self.can_manage_filial(scope, codigo_filial, user=user):
            raise PermissionError("Sem permissão para alterar dados nesta filial.")
