"""Port do gateway S2S de notificações (C6).

A Minha DELPI/Core API é a única dona de notificações do usuário autenticado:
o Production Control apenas dispara o dispatch depois do fato operacional já
persistido. Nenhuma tabela/sino/socket paralelo nasce desta port.
"""

from __future__ import annotations

from typing import Any, Protocol


class NotificationGatewayPort(Protocol):
    """Dispara um dispatch de notificação na Core API."""

    def dispatch(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /integrations/notifications.

        Levanta NotificationGatewayUnavailable / Unauthorized /
        ContractError — o chamador decide a criticidade (aqui: nunca
        crítica; notificação é camada de atenção, não de verdade)."""
        ...
