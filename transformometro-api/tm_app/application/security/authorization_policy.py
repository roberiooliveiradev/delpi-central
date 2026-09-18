"""Checagem dos dois códigos já resolvidos pela Core.

Não resolve papel, grupo nem assignment. Não cria hierarquia:
`manage` não implica `access`. Filial não entra aqui.
"""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
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
        return has_permission(user, ACCESS_PERMISSION)

    def has_manage(self, user: Any | None) -> bool:
        if user is None:
            return False
        if getattr(user, "is_superadmin", False):
            return True
        return has_permission(user, MANAGE_PERMISSION)

    def require_access(self, user: Any | None) -> None:
        self._require_user(user)
        if self.has_access(user):
            return
        raise AuthorizationDenied("Sem permissão transformometro.access.")

    def require_manage(self, user: Any | None) -> None:
        self._require_user(user)
        if self.has_manage(user):
            return
        raise AuthorizationDenied("Sem permissão transformometro.manage.")

    @staticmethod
    def _require_user(user: Any | None) -> None:
        if user is None:
            raise AuthorizationDenied("Usuário não autenticado.", status_code=401)
