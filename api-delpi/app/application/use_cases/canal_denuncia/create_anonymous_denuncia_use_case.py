from __future__ import annotations

import logging
from typing import Any

from app.application.services.canal_denuncia_email_content_service import (
    EMAIL_SUBJECT,
    build_denuncia_email_html,
)
from app.infrastructure.persistence.plugins.repositories.canal_denuncia.postgres_canal_denuncia_repository import (
    PostgresCanalDenunciaRepository,
)
from app.infrastructure.providers.microsoft_graph.microsoft_graph_mail_client import (
    GraphMailError,
    MicrosoftGraphMailClient,
    sanitize_graph_error,
)

logger = logging.getLogger(__name__)


class CreateAnonymousDenunciaUseCase:
    def __init__(
        self,
        repository: PostgresCanalDenunciaRepository,
        mail_client: MicrosoftGraphMailClient,
    ) -> None:
        self._repository = repository
        self._mail_client = mail_client

    def execute(self, *, description: str) -> dict[str, Any]:
        row = self._repository.create_anonymous_denuncia(description=description)
        denuncia_id = row["id"]
        created_at = row["created_at"]
        self._try_send_notification(
            denuncia_id=denuncia_id,
            description=row["description"],
            created_at=created_at,
        )
        return {
            "id": denuncia_id,
            "createdAt": created_at.isoformat()
            if hasattr(created_at, "isoformat")
            else str(created_at),
        }

    def _try_send_notification(
        self,
        *,
        denuncia_id: str,
        description: str,
        created_at: Any,
    ) -> None:
        try:
            html_body = build_denuncia_email_html(
                description=description,
                created_at=created_at,
            )
            self._mail_client.send_mail(subject=EMAIL_SUBJECT, html_body=html_body)
            self._repository.mark_email_sent(denuncia_id=denuncia_id)
        except GraphMailError as exc:
            error_message = sanitize_graph_error(str(exc))
            logger.warning(
                "canal_denuncia_email_failed denuncia_id=%s reason=%s",
                denuncia_id,
                error_message,
            )
            try:
                self._repository.mark_email_failed(
                    denuncia_id=denuncia_id,
                    error_message=error_message,
                )
            except Exception:
                logger.exception(
                    "canal_denuncia_email_status_update_failed denuncia_id=%s",
                    denuncia_id,
                )
        except Exception:
            logger.exception(
                "canal_denuncia_email_unexpected_error denuncia_id=%s",
                denuncia_id,
            )
            try:
                self._repository.mark_email_failed(
                    denuncia_id=denuncia_id,
                    error_message="Falha inesperada ao enviar e-mail da denúncia.",
                )
            except Exception:
                logger.exception(
                    "canal_denuncia_email_status_update_failed denuncia_id=%s",
                    denuncia_id,
                )
