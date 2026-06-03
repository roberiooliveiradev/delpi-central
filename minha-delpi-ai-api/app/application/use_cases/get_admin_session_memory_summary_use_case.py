from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.services.chat_session_memory_admin_metrics_service import (
    ChatSessionMemoryAdminMetricsService,
)
from app.infrastructure.config.settings import Settings


class _SessionMemoryFeedbackRepositoryPort(Protocol):
    def list_feedback_since(self, *, since: datetime) -> list[dict[str, Any]]: ...


class GetAdminSessionMemorySummaryUseCase:
    def __init__(
        self,
        audit_repository: AuditRepositoryPort,
        feedback_repository: _SessionMemoryFeedbackRepositoryPort | None = None,
    ):
        self.audit_repository = audit_repository
        self.feedback_repository = feedback_repository

    def execute(self, *, hours: int = 168) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        usage = self.audit_repository.get_session_memory_summary(hours=safe_hours)

        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)
        feedback_repo = self.feedback_repository or self._default_feedback_repository()
        rows = feedback_repo.list_feedback_since(since=since)
        feedback = ChatSessionMemoryAdminMetricsService.aggregate_feedback_rows(rows)

        return ChatSessionMemoryAdminMetricsService.merge_usage_and_feedback(usage, feedback)

    @staticmethod
    def _default_feedback_repository() -> _SessionMemoryFeedbackRepositoryPort:
        from app.infrastructure.persistence.postgres_chat_message_feedback_repository import (
            PostgresChatMessageFeedbackRepository,
        )

        return PostgresChatMessageFeedbackRepository()
