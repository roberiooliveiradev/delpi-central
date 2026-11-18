"""Evento pós-confirmação GLPI para o sininho Minha Delpi (#1616).

Apenas o solicitante resolvido para UUID do diretório pode receber.
A plataforma (Core) aplica RBAC do Helpdesk e preferências do usuário.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Literal
from uuid import UUID

import httpx

from helpdesk_app.config import settings
from helpdesk_app.application.followup_ticket_notification_service import FollowupTicketNotice

logger = logging.getLogger("helpdesk.solved_notifications")
DeliveryResult = Literal["sent", "ignored", "retry"]
CATEGORY = "helpdesk_ticket_solved"
SOURCE_APP = "helpdesk"
EVENT = "helpdesk_ticket_solved"


@dataclass(frozen=True)
class SolvedTicketNotice:
    ticket_id: int
    solution_id: int
    recipient_user_id: str
    ticket_title: str

    def __post_init__(self) -> None:
        if self.ticket_id <= 0 or self.solution_id <= 0:
            raise ValueError("ticket_id e solution_id devem ser positivos.")
        # Não aceitar GLPI user id como destinatário da Core API.
        object.__setattr__(self, "recipient_user_id", str(UUID(self.recipient_user_id)))
        object.__setattr__(self, "ticket_title", (self.ticket_title or "").strip()[:250])

    @property
    def event_key(self) -> str:
        return f"helpdesk:ticket-solved:{self.ticket_id}:{self.solution_id}"

    def payload(self) -> dict:
        short_title = self.ticket_title[:150]
        return {
            "title": f"Chamado #{self.ticket_id} solucionado",
            "message": (
                f'O chamado #{self.ticket_id} "{short_title}" foi solucionado. '
                "Abra o chamado para consultar a solução registrada."
            ),
            "type": "success",
            "category": CATEGORY,
            "sourceApp": SOURCE_APP,
            "userIds": [self.recipient_user_id],
            "action": {
                "type": "portal_route",
                "label": "Ver solução",
                "target": f"/apps/helpdesk/tickets/{self.ticket_id}",
            },
            "metadata": {
                "source": SOURCE_APP,
                "event": EVENT,
                "ticketId": self.ticket_id,
                "solutionId": self.solution_id,
                "dedupeKey": self.event_key,
            },
        }


class CoreHelpdeskNotificationGateway:
    """Reutiliza POST /integrations/notifications; nunca contorna o Core."""

    def __init__(
        self,
        *,
        core_api_url: str | None = None,
        service_token: str | None = None,
        timeout: float = 6.0,
        http_post: Callable | None = None,
    ) -> None:
        self.core_api_url = (core_api_url or settings.CORE_API_URL).rstrip("/")
        self.service_token = (
            service_token if service_token is not None
            else settings.CORE_API_INTEGRATIONS_SERVICE_TOKEN
        )
        self.timeout = timeout
        self._http_post = http_post or httpx.post

    def send(self, notice: SolvedTicketNotice | "FollowupTicketNotice") -> DeliveryResult:
        if not self.service_token:
            logger.warning("helpdesk_solved_notifications_missing_core_token")
            return "retry"
        try:
            response = self._http_post(
                f"{self.core_api_url}/integrations/notifications",
                headers={
                    "Authorization": f"Bearer {self.service_token}",
                    "X-Delpi-Service-Token": self.service_token,
                    "Content-Type": "application/json",
                },
                json=notice.payload(),
                timeout=self.timeout,
            )
        except Exception:
            logger.exception("helpdesk_solved_notification_core_unavailable event=%s", notice.event_key)
            return "retry"

        if 200 <= response.status_code < 300:
            return "sent"
        # Categoria silenciada, usuário desativado ou app não autorizado:
        # o Core tem a palavra final. Não insistir em destino sem acesso.
        if response.status_code in (400, 422):
            logger.warning(
                "helpdesk_solved_notification_rejected event=%s status=%s",
                notice.event_key, response.status_code,
            )
            return "ignored"
        logger.warning(
            "helpdesk_solved_notification_retry event=%s status=%s",
            notice.event_key, response.status_code,
        )
        return "retry"
