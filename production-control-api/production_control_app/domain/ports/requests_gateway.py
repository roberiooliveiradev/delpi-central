"""Port do gateway S2S → Requests API (P2 — Problemas de Processo).

O Requests API é o dono canônico das solicitações do Minhas Solicitações: o
Production Control apenas encaminha o snapshot do cockpit. Nenhuma tabela,
fila ou réplica de request nasce desta port — indisponibilidade vira erro
para o operador, nunca um "request fantasma" local.
"""

from __future__ import annotations

from typing import Any, Protocol


class RequestsGatewayPort(Protocol):
    """Cria solicitação no Requests API via POST /integrations/requests."""

    def create_request(
        self,
        *,
        body: dict[str, Any],
        idempotency_key: str,
    ) -> dict[str, Any]:
        """Levanta RequestsGatewayUnavailable / Unauthorized / Rejected.

        O caller repassa a MESMA Idempotency-Key recebida do cockpit — a
        chave atravessa ponta a ponta e a dedup vive no Requests API."""
        ...
