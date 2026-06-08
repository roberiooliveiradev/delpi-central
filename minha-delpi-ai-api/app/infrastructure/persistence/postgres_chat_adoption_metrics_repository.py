from __future__ import annotations

from datetime import datetime

from app.domain.ports.chat_adoption_metrics_repository_port import (
    ChatAdoptionMetricsRepositoryPort,
)
from app.extensions.db import db
from app.infrastructure.db.models.audit_log_model import AiAuditLogModel
from app.infrastructure.db.models.chat_session_model import AiChatSessionModel


class PostgresChatAdoptionMetricsRepository(ChatAdoptionMetricsRepositoryPort):
    def count_audit_action(self, action: str, *, since: datetime) -> int:
        return (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action == action)
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

    def count_audit_actions(self, actions: tuple[str, ...], *, since: datetime) -> int:
        return (
            db.session.query(AiAuditLogModel)
            .filter(AiAuditLogModel.action.in_(actions))
            .filter(AiAuditLogModel.created_at >= since)
            .count()
        )

    def count_active_sessions(self, *, since: datetime) -> int:
        return (
            db.session.query(AiChatSessionModel)
            .filter(AiChatSessionModel.updated_at >= since)
            .count()
        )

    def count_active_users(self, *, since: datetime) -> int:
        return (
            db.session.query(AiChatSessionModel.user_id)
            .filter(AiChatSessionModel.updated_at >= since)
            .distinct()
            .count()
        )
