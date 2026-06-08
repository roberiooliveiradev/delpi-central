from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.ports.audit_repository_port import AuditRepositoryPort
from app.domain.ports.chat_message_feedback_repository_port import (
    ChatMessageFeedbackRepositoryPort,
)
from app.domain.services.chat_text_task_admin_metrics_service import (
    ChatTextTaskAdminMetricsService,
)
from app.infrastructure.config.settings import Settings


class GetAdminTextTaskSummaryUseCase:
    def __init__(
        self,
        audit_repository: AuditRepositoryPort,
        feedback_repository: ChatMessageFeedbackRepositoryPort | None = None,
    ):
        self.audit_repository = audit_repository
        self.feedback_repository = feedback_repository

    def execute(self, *, hours: int = 168) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        usage = self.audit_repository.get_text_task_summary(hours=safe_hours)

        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)
        feedback_repo = self.feedback_repository or self._default_feedback_repository()
        rows = feedback_repo.list_feedback_since(since=since)
        feedback = ChatTextTaskAdminMetricsService.aggregate_feedback_rows(rows)

        return ChatTextTaskAdminMetricsService.merge_usage_and_feedback(usage, feedback)

    @staticmethod
    def _default_feedback_repository() -> ChatMessageFeedbackRepositoryPort:
        from app.composition.repository_composer import make_chat_message_feedback_repository

        return make_chat_message_feedback_repository()
