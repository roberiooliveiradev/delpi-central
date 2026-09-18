"""Política de autorização do Transformômetro.

HTTP, MCP e GPT Actions chamam estes métodos. Não decidem sozinhos.
`manage` não implica `access`. Filial não entra aqui.
O recálculo interno depois de escrita ou importação não passa por aqui.
"""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_any_permission, has_permission

from tm_app.application.security.transformometro_permissions import (
    LEGACY_NORMAL_USE_PERMISSIONS,
    TRANSFORMOMETRO_ACCESS,
    TRANSFORMOMETRO_DASHBOARD_RECALCULATE,
    TRANSFORMOMETRO_DATA_TRANSFER,
    TRANSFORMOMETRO_MANAGE,
    TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE,
)


class AuthorizationDenied(PermissionError):
    def __init__(self, message: str, *, status_code: int = 403) -> None:
        super().__init__(message)
        self.status_code = status_code


class TransformometroAuthorizationPolicy:
    def has_access(self, user: Any | None) -> bool:
        if user is None:
            return False
        if getattr(user, "is_superadmin", False):
            return True
        return has_any_permission(
            user,
            (TRANSFORMOMETRO_ACCESS, *LEGACY_NORMAL_USE_PERMISSIONS),
        )

    def has_manage(self, user: Any | None) -> bool:
        """Só o código novo. Não herda access e não aceita legado."""
        if user is None:
            return False
        if getattr(user, "is_superadmin", False):
            return True
        return has_permission(user, TRANSFORMOMETRO_MANAGE)

    def require_access(self, user: Any | None) -> None:
        self._require_user(user)
        if self.has_access(user):
            return
        raise AuthorizationDenied(
            "Sem permissão transformometro.access "
            "(ou uso legado, inclusive transformometro.view)."
        )

    def require_manage(self, user: Any | None) -> None:
        self._require_user(user)
        if self.has_manage(user):
            return
        raise AuthorizationDenied("Sem permissão transformometro.manage.")

    def require_data_transfer(self, user: Any | None) -> None:
        self._require_user(user)
        if self.has_manage(user) or has_permission(user, TRANSFORMOMETRO_DATA_TRANSFER):
            return
        raise AuthorizationDenied(
            "Sem permissão transformometro.manage ou transformometro.data.transfer."
        )

    def require_dashboard_recalculate(self, user: Any | None) -> None:
        """Comando do usuário. Uso normal não recalcula."""
        self._require_user(user)
        if self.has_manage(user) or has_permission(
            user, TRANSFORMOMETRO_DASHBOARD_RECALCULATE
        ):
            return
        raise AuthorizationDenied(
            "Sem permissão transformometro.manage ou transformometro.dashboard.recalculate."
        )

    def require_shared_resources(self, user: Any | None) -> None:
        self._require_user(user)
        if self.has_manage(user) or has_permission(
            user, TRANSFORMOMETRO_SHARED_RESOURCES_MANAGE
        ):
            return
        raise AuthorizationDenied(
            "Sem permissão transformometro.manage ou transformometro.shared-resources.manage."
        )

    @staticmethod
    def _require_user(user: Any | None) -> None:
        if user is None:
            raise AuthorizationDenied("Usuário não autenticado.", status_code=401)
