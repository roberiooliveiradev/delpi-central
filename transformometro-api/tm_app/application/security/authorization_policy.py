"""Política de autorização do Transformômetro para operações user-facing.

Adapters HTTP, MCP e GPT Actions chamam estes métodos. Não decidem sozinhos.
O recálculo interno depois de escrita ou importação não passa por aqui.
"""

from __future__ import annotations

from typing import Any

from delpi_auth.authz_core import has_permission

from tm_app.application.security.transformometro_permissions import (
    GLOBAL_MANAGE_PERMISSIONS,
    TRANSFORMOMETRO_DASHBOARD_RECALCULATE,
    TRANSFORMOMETRO_DATA_TRANSFER,
    TRANSFORMOMETRO_REVISIONS_MANAGE,
)


class AuthorizationDenied(PermissionError):
    def __init__(self, message: str, *, status_code: int = 403) -> None:
        super().__init__(message)
        self.status_code = status_code


class TransformometroAuthorizationPolicy:
    def require_data_transfer(self, user: Any | None) -> None:
        """Export, preview e import. Código atual, sem trocar para manage."""
        self._require_user(user)
        if getattr(user, "is_superadmin", False):
            return
        if has_permission(user, TRANSFORMOMETRO_DATA_TRANSFER):
            return
        raise AuthorizationDenied("Sem permissão transformometro.data.transfer.")

    def require_dashboard_recalculate(self, user: Any | None) -> None:
        """Mesma regra já usada por MCP e GPT Actions, agora também no HTTP."""
        self._require_user(user)
        if getattr(user, "is_superadmin", False):
            return
        if has_permission(user, TRANSFORMOMETRO_DASHBOARD_RECALCULATE):
            return
        for code in (TRANSFORMOMETRO_REVISIONS_MANAGE, *GLOBAL_MANAGE_PERMISSIONS):
            if has_permission(user, code):
                return
        raise AuthorizationDenied(
            "Sem permissão transformometro.dashboard.recalculate (ou manage equivalente)."
        )

    @staticmethod
    def _require_user(user: Any | None) -> None:
        if user is None:
            raise AuthorizationDenied("Usuário não autenticado.", status_code=401)
