from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)

_ALLOWED_EMAIL_STATUS = frozenset({"pending", "sent", "failed"})
_MAX_EMAIL_ERROR_LEN = 480


class PostgresCanalDenunciaRepository(PluginBaseRepository):
    """Persistência de denúncias anônimas — sem campos de identidade."""

    def create_anonymous_denuncia(self, *, description: str) -> dict[str, Any]:
        normalized = description.strip()
        if len(normalized) < 10:
            raise PluginsRepositoryError(
                "A descrição da denúncia deve ter ao menos 10 caracteres."
            )

        row = self.execute_returning_one(
            """
            INSERT INTO canal_denuncia.denuncias (description)
            VALUES (%s)
            RETURNING id, description, created_at, email_status, email_attempts
            """,
            (normalized,),
        )
        if not row:
            raise PluginsRepositoryError("Falha ao registrar a denúncia.")
        return {
            "id": str(row["id"]),
            "description": row["description"],
            "created_at": row["created_at"],
            "email_status": row.get("email_status") or "pending",
            "email_attempts": int(row.get("email_attempts") or 0),
        }

    def mark_email_sent(self, *, denuncia_id: str) -> None:
        self._update_email_delivery(
            denuncia_id=denuncia_id,
            email_status="sent",
            email_last_error=None,
            email_sent_at=datetime.now(timezone.utc),
        )

    def mark_email_failed(self, *, denuncia_id: str, error_message: str) -> None:
        sanitized = " ".join(str(error_message or "").split())
        if len(sanitized) > _MAX_EMAIL_ERROR_LEN:
            sanitized = sanitized[: _MAX_EMAIL_ERROR_LEN - 1] + "…"
        if not sanitized:
            sanitized = "Falha ao enviar e-mail da denúncia."
        self._update_email_delivery(
            denuncia_id=denuncia_id,
            email_status="failed",
            email_last_error=sanitized,
            email_sent_at=None,
        )

    def _update_email_delivery(
        self,
        *,
        denuncia_id: str,
        email_status: str,
        email_last_error: str | None,
        email_sent_at: datetime | None,
    ) -> None:
        if email_status not in _ALLOWED_EMAIL_STATUS:
            raise PluginsRepositoryError("Status de e-mail inválido.")
        self.execute(
            """
            UPDATE canal_denuncia.denuncias
            SET email_status = %s,
                email_attempts = email_attempts + 1,
                email_last_error = %s,
                email_sent_at = %s,
                updated_at = NOW()
            WHERE id = %s::uuid
            """,
            (email_status, email_last_error, email_sent_at, denuncia_id),
        )
