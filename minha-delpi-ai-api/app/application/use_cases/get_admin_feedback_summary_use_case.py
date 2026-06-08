from datetime import datetime, timedelta, timezone

from app.domain.ports.chat_message_feedback_repository_port import (
    ChatMessageFeedbackRepositoryPort,
)
from app.domain.services.chat_feedback_admin_metrics_service import (
    ChatFeedbackAdminMetricsService,
)


def _default_feedback_repository() -> ChatMessageFeedbackRepositoryPort:
    from app.composition.repository_composer import make_chat_message_feedback_repository

    return make_chat_message_feedback_repository()


class GetAdminFeedbackSummaryUseCase:
    def __init__(
        self,
        feedback_repository: ChatMessageFeedbackRepositoryPort | None = None,
    ):
        self.feedback_repository = feedback_repository or _default_feedback_repository()

    def execute(self, *, hours: int = 168) -> dict:
        from app.infrastructure.config.settings import Settings

        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)
        rows = self.feedback_repository.list_feedback_since(since=since)

        return ChatFeedbackAdminMetricsService.aggregate_rows(
            rows,
            hours=safe_hours,
            since_iso=since.isoformat(),
        )
