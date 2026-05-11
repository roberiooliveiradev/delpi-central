from uuid import UUID

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.extensions.db import db
from app.infrastructure.db.models.audit_log_model import AiAuditLogModel


class PostgresAuditRepository(AuditRepositoryPort):
    def log(
        self,
        user_id: UUID | None,
        action: str,
        prompt_hash: str | None = None,
        context: str | None = None,
        tool_calls: list | None = None,
        metadata: dict | None = None,
    ) -> None:
        model = AiAuditLogModel(
            user_id=user_id,
            action=action,
            prompt_hash=prompt_hash,
            context=context,
            tool_calls=tool_calls,
            audit_metadata=metadata,
        )

        db.session.add(model)
        db.session.flush()
