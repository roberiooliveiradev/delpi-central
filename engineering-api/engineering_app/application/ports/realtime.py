"""Porta de tempo real — ENG-REALTIME-01.

Contrato neutro de invalidação: a aplicação publica um evento leve
**após** o commit oficial; o adapter (hub WebSocket) entrega aos sockets
autorizados e o cliente faz HTTP refetch na API oficial.

Domain/application não conhecem FastAPI, WebSocket, rooms ou tokens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class RealtimeEvent:
    """Evento leve de invalidação — nunca transporta ficha, documentos,
    fornecedores, Part Number ou conteúdo técnico do recurso."""

    domain: str  # ex.: "product-registration"
    resource_type: str  # ex.: "request"
    resource_id: str
    reason: str  # operação canônica (ex.: "start", "resubmit_correction")
    occurred_at: str  # ISO-8601 UTC
    event_id: str
    version: int | None = None
    status: str | None = None
    actor_user_id: str | None = None
    actor_client_id: str | None = None
    recipient_user_ids: tuple[str, ...] = field(default_factory=tuple)
    # ``queue_impact`` True → o evento afeta posição/estado na fila do
    # domínio (criação, transições, conclusão). Eventos puramente
    # historiográficos (anexo, comentário) marcam False.
    queue_impact: bool = True


class RealtimePublisher(Protocol):
    """Publicação best-effort pós-commit.

    Falha de entrega NUNCA desfaz a mutação já persistida — adapters
    registram e seguem. Não é evento durável de domínio nem outbox.
    """

    def publish(self, event: RealtimeEvent) -> None: ...


class NullRealtimePublisher:
    """Default quando a feature flag desliga o tempo real."""

    def publish(self, event: RealtimeEvent) -> None:
        return None
