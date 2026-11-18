"""Notificação de novo retorno público de chamado para o solicitante (#1618)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from helpdesk_app.application.services.message_html_sanitizer import (
    message_html_to_plain_text,
)

CATEGORY = "helpdesk_ticket_followup"
EVENT = "helpdesk_ticket_followup"
PREVIEW_LIMIT = 160


def preview_from_html(raw_html: str | None) -> str:
    """Texto plano breve e sem URLs embutidas de HTML ou imagens do editor."""
    text = message_html_to_plain_text(raw_html)
    text = " ".join(text.replace("\u200b", " ").split())
    if len(text) <= PREVIEW_LIMIT:
        return text
    return text[: PREVIEW_LIMIT - 1].rstrip() + "…"


@dataclass(frozen=True)
class FollowupTicketNotice:
    ticket_id: int
    followup_id: int
    recipient_user_id: str
    ticket_title: str
    preview: str

    def __post_init__(self) -> None:
        if self.ticket_id <= 0 or self.followup_id <= 0:
            raise ValueError("ticket_id e followup_id devem ser positivos")
        # Não aceitar id numérico do GLPI como destinatário Core.
        object.__setattr__(self, "recipient_user_id", str(UUID(self.recipient_user_id)))
        object.__setattr__(self, "ticket_title", " ".join((self.ticket_title or "").split())[:250])
        # A camada persistente nunca recebe HTML bruto.
        object.__setattr__(self, "preview", preview_from_html(self.preview))

    @property
    def event_key(self) -> str:
        return f"helpdesk:ticket-followup:{self.ticket_id}:{self.followup_id}"

    def payload(self) -> dict:
        suffix = f" Prévia: {self.preview}" if self.preview else " Abra o chamado para ler a mensagem."
        title = self.ticket_title or "Sem título"
        return {
            "title": f"Novo retorno no chamado #{self.ticket_id}",
            "message": f"#{self.ticket_id} · {title}.{suffix}",
            "type": "info",
            "category": CATEGORY,
            "sourceApp": "helpdesk",
            "userIds": [self.recipient_user_id],
            "action": {
                "type": "portal_route",
                "label": "Ver retorno",
                "target": f"/apps/helpdesk/tickets/{self.ticket_id}",
            },
            "metadata": {
                "source": "helpdesk",
                "event": EVENT,
                "ticketId": self.ticket_id,
                "followupId": self.followup_id,
                "dedupeKey": self.event_key,
            },
        }
