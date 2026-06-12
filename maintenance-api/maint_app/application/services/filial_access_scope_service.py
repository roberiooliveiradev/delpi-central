from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from delpi_auth.authz_core import has_permission

from maint_app.application.security.maintenance_permissions import (
    _SUBMODULE_MANAGE_FILIAL_MARKER,
    _SUBMODULE_VIEW_FILIAL_MARKER,
    codigos_from_submodule_filial_permissions,
    submodule_manage_permission,
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
    manage_codigos: frozenset[str]

    @property
    def is_unrestricted(self) -> bool:
        return self.mode == "unrestricted"

    @property
    def scoped_manage(self) -> bool:
        return bool(self.manage_codigos)

    def meta(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "allowed_filiais": sorted(self.allowed_codigos),
            "manage_filiais": sorted(self.manage_codigos),
            "scoped_manage": self.scoped_manage,
        }


class FilialAccessScopeService:
    def resolve(self, user: Any | None) -> FilialAccessScope:
        if user is None or getattr(user, "is_superadmin", False):
            return FilialAccessScope(
                mode="unrestricted",
                allowed_codigos=frozenset(),
                manage_codigos=frozenset(),
            )

        permissions = list(getattr(user, "permissions", []) or [])
        branch_view = codigos_from_submodule_filial_permissions(
            permissions,
            marker=_SUBMODULE_VIEW_FILIAL_MARKER,
        )
        branch_manage = codigos_from_submodule_filial_permissions(
            permissions,
            marker=_SUBMODULE_MANAGE_FILIAL_MARKER,
        )

        if branch_view:
            return FilialAccessScope(
                mode="scoped",
                allowed_codigos=frozenset(branch_view),
                manage_codigos=frozenset(branch_manage),
            )

        return FilialAccessScope(
            mode="scoped",
            allowed_codigos=frozenset(),
            manage_codigos=frozenset(),
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
        submodule_id: str = "mini-aplicadores",
    ) -> bool:
        codigo = _normalize_codigo(codigo_filial)
        if not codigo:
            return False
        if user is not None and getattr(user, "is_superadmin", False):
            return True

        manage_perm = submodule_manage_permission(submodule_id, codigo)
        if user is not None and has_permission(user, manage_perm):
            return True

        if scope.is_unrestricted:
            return True

        return codigo in scope.manage_codigos

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
            raise PermissionError("Sem permissão para acessar dados desta filial.")

    def assert_manage_filial(
        self,
        scope: FilialAccessScope,
        codigo_filial: str,
        *,
        user: Any | None,
        submodule_id: str = "mini-aplicadores",
    ) -> None:
        if not self.can_manage_filial(
            scope,
            codigo_filial,
            user=user,
            submodule_id=submodule_id,
        ):
            raise PermissionError("Sem permissão para alterar dados nesta filial.")

    def resolve_default_filial(
        self,
        scope: FilialAccessScope,
        filiais: list[dict[str, Any]],
    ) -> str | None:
        if not filiais:
            return None
        if len(filiais) == 1:
            return str(filiais[0]["id"])
        return None
