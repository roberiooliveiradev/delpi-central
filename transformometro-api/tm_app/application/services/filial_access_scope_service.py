from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from delpi_auth.authz_core import has_any_permission, has_permission

from tm_app.application.security.transformometro_permissions import (
    BRANCH_MANAGE_PERMISSIONS,
    BRANCH_VIEW_PERMISSIONS,
    GLOBAL_MANAGE_PERMISSIONS,
    MANAGE_FILIAL_PERMISSIONS,
    TRANSFORMOMETRO_VIEW,
    TRANSFORMOMETRO_VIEW_CONSOLIDATED,
    VIEW_FILIAL_PERMISSIONS,
)


@dataclass(frozen=True)
class FilialAccessScope:
    """Escopo de filiais permitido para leitura/escrita do usuário autenticado."""

    mode: str
    allowed_codigos: frozenset[str]
    can_view_consolidated: bool
    scoped_manage: bool

    @property
    def is_unrestricted(self) -> bool:
        return self.mode == "unrestricted"

    def meta(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "allowed_filiais": sorted(self.allowed_codigos),
            "can_view_consolidated": self.can_view_consolidated,
            "scoped_manage": self.scoped_manage,
        }


class FilialAccessScopeService:
    """Resolve e aplica RBAC por filial (server-side)."""

    def resolve(self, user: Any | None) -> FilialAccessScope:
        if user is None:
            return FilialAccessScope(
                mode="unrestricted",
                allowed_codigos=frozenset(),
                can_view_consolidated=True,
                scoped_manage=False,
            )

        if getattr(user, "is_superadmin", False):
            return FilialAccessScope(
                mode="unrestricted",
                allowed_codigos=frozenset(),
                can_view_consolidated=True,
                scoped_manage=False,
            )

        permissions = list(getattr(user, "permissions", []) or [])
        branch_view = self._branch_codes_from_permissions(
            permissions,
            VIEW_FILIAL_PERMISSIONS,
        )
        branch_manage = self._branch_codes_from_permissions(
            permissions,
            MANAGE_FILIAL_PERMISSIONS,
        )

        if branch_view:
            return FilialAccessScope(
                mode="scoped",
                allowed_codigos=frozenset(branch_view),
                can_view_consolidated=TRANSFORMOMETRO_VIEW_CONSOLIDATED in permissions,
                scoped_manage=bool(branch_manage),
            )

        return FilialAccessScope(
            mode="unrestricted",
            allowed_codigos=frozenset(),
            can_view_consolidated=True,
            scoped_manage=bool(branch_manage),
        )

    @staticmethod
    def _branch_codes_from_permissions(
        permissions: list[str],
        mapping: dict[str, str],
    ) -> list[str]:
        return sorted(
            codigo
            for codigo, perm in mapping.items()
            if perm in permissions
        )

    def can_view_filial(self, scope: FilialAccessScope, codigo_filial: str | None) -> bool:
        codigo = _normalize_codigo(codigo_filial)
        if not codigo:
            return False
        if scope.is_unrestricted:
            return True
        return codigo in scope.allowed_codigos

    def can_view_consolidated(self, scope: FilialAccessScope) -> bool:
        if scope.is_unrestricted:
            return True
        return scope.can_view_consolidated

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

        if scope.is_unrestricted and not scope.scoped_manage:
            return has_any_permission(user, GLOBAL_MANAGE_PERMISSIONS) if user else False

        manage_perm = MANAGE_FILIAL_PERMISSIONS.get(codigo)
        if manage_perm and manage_perm in permissions:
            return True

        if scope.is_unrestricted and has_any_permission(user, GLOBAL_MANAGE_PERMISSIONS):
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
        return [
            item
            for item in filiais
            if _normalize_codigo(item.get("id") or item.get("codigo_filial")) in allowed
        ]

    def filter_rows_by_filial(
        self,
        rows: list[dict[str, Any]],
        scope: FilialAccessScope,
        *,
        codigo_key: str = "filial_id",
        alt_codigo_key: str | None = "codigo_filial",
    ) -> list[dict[str, Any]]:
        if scope.is_unrestricted:
            return rows
        filtered: list[dict[str, Any]] = []
        for row in rows:
            codigo = _normalize_codigo(row.get(codigo_key))
            if not codigo and alt_codigo_key:
                codigo = _normalize_codigo(row.get(alt_codigo_key))
            if codigo and self.can_view_filial(scope, codigo):
                filtered.append(row)
        return filtered

    def user_has_branch_view_permissions(self, user: Any | None) -> bool:
        if user is None:
            return False
        permissions = getattr(user, "permissions", []) or []
        return any(perm in permissions for perm in BRANCH_VIEW_PERMISSIONS)

    def user_has_legacy_view(self, user: Any | None) -> bool:
        if user is None:
            return False
        return has_permission(user, TRANSFORMOMETRO_VIEW)


def _normalize_codigo(value: Any | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
