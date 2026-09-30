"""Administração humana do catálogo global de motivos de parada.

Este BFF **não** é o owner do catálogo: validação industrial, unicidade,
imutabilidade de ``code``, proteção do motivo ``setup`` e soft-delete são
autoridade do ``production-control-api``. Aqui ficam apenas autorização
humana (RBAC), encaminhamento ao gateway S2S e allowlist do contrato.

O catálogo é global — nenhuma operação recebe ``branch`` nem exige
permissão de filial.
"""

from __future__ import annotations

from typing import Any

from delpi_mes_app.core.security import (
    MES_ACCESS,
    MES_DOWNTIME_REASONS_MANAGE,
    can,
    is_human_user,
)
from delpi_mes_app.domain.errors import HumanPrincipalRequired
from delpi_mes_app.domain.ports.production_control_mes_gateway import (
    ProductionControlMesGatewayPort,
)

_REASON_FIELDS = (
    "code", "label", "category", "requiresNote",
    "active", "sortOrder", "createdAt", "updatedAt",
)


class MesDowntimeReasonAdminService:
    def __init__(self, gateway: ProductionControlMesGatewayPort) -> None:
        self._gateway = gateway

    def list_reasons(self, user: Any) -> dict[str, Any]:
        self._authorize_management(user)
        data = self._gateway.list_downtime_reasons()
        return {"items": [self._view(item) for item in data.get("items", [])]}

    def create_reason(
        self,
        user: Any,
        *,
        code: str,
        label: str,
        category: str,
        requires_note: bool,
        sort_order: int,
    ) -> dict[str, Any]:
        self._authorize_management(user)
        data = self._gateway.create_downtime_reason(
            {
                "code": code,
                "label": label,
                "category": category,
                "requiresNote": requires_note,
                "sortOrder": sort_order,
            }
        )
        return self._view(data)

    def update_reason(
        self,
        user: Any,
        code: str,
        *,
        label: str,
        category: str,
        requires_note: bool,
        sort_order: int,
    ) -> dict[str, Any]:
        self._authorize_management(user)
        data = self._gateway.update_downtime_reason(
            code,
            {
                "label": label,
                "category": category,
                "requiresNote": requires_note,
                "sortOrder": sort_order,
            },
        )
        return self._view(data)

    def set_reason_active(self, user: Any, code: str, *, active: bool) -> dict[str, Any]:
        self._authorize_management(user)
        data = self._gateway.set_downtime_reason_active(code, active=active)
        return self._view(data)

    @staticmethod
    def _authorize_management(user: Any) -> None:
        if not is_human_user(user):
            raise HumanPrincipalRequired(
                "Administração do catálogo exige um usuário autenticado."
            )
        if not can(user, MES_ACCESS):
            raise PermissionError("Sem permissão para acessar o Delpi MES.")
        if not can(user, MES_DOWNTIME_REASONS_MANAGE):
            raise PermissionError("Sem permissão para administrar motivos de parada.")

    @staticmethod
    def _view(item: dict[str, Any]) -> dict[str, Any]:
        return {field: item.get(field) for field in _REASON_FIELDS}
