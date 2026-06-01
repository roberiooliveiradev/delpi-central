from datetime import datetime, timedelta, timezone

from app.domain.services.chat_feedback_admin_metrics_service import (
    ChatFeedbackAdminMetricsService,
)
from app.infrastructure.persistence.postgres_chat_message_feedback_repository import (
    PostgresChatMessageFeedbackRepository,
)


class GetAdminFeedbackSummaryUseCase:
    def __init__(
        self,
        feedback_repository: PostgresChatMessageFeedbackRepository | None = None,
    ):
        self.feedback_repository = feedback_repository or PostgresChatMessageFeedbackRepository()

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
