from datetime import datetime, timedelta, timezone

from app.application.use_cases.admin_security_use_cases import GetAdminSecuritySummaryUseCase
from app.application.use_cases.get_admin_feedback_summary_use_case import (
    GetAdminFeedbackSummaryUseCase,
)
from app.application.use_cases.get_admin_metrics_summary_use_case import (
    GetAdminMetricsSummaryUseCase,
)
from app.domain.services.chat_quality_adoption_metrics_service import (
    ChatQualityAdoptionMetricsService,
)
from app.domain.services.chat_quality_unified_metrics_service import (
    ChatQualityUnifiedMetricsService,
)
from app.infrastructure.config.settings import Settings


class GetAdminQualityUnifiedSummaryUseCase:
    def __init__(
        self,
        *,
        feedback_use_case: GetAdminFeedbackSummaryUseCase | None = None,
        metrics_use_case: GetAdminMetricsSummaryUseCase,
        security_use_case: GetAdminSecuritySummaryUseCase,
    ):
        self._feedback_use_case = feedback_use_case or GetAdminFeedbackSummaryUseCase()
        self._metrics_use_case = metrics_use_case
        self._security_use_case = security_use_case

    def execute(self, *, hours: int = 168) -> dict:
        safe_hours = max(1, min(int(hours), Settings.ADMIN_METRICS_MAX_HOURS))
        since = datetime.now(timezone.utc) - timedelta(hours=safe_hours)

        feedback = self._feedback_use_case.execute(hours=safe_hours)
        metrics = self._metrics_use_case.execute(hours=safe_hours)
        security = self._security_use_case.execute(hours=min(safe_hours, 168))
        adoption = ChatQualityAdoptionMetricsService.snapshot(hours=safe_hours)

        return ChatQualityUnifiedMetricsService.build(
            feedback=feedback,
            metrics=metrics,
            security=security,
            adoption=adoption,
            hours=safe_hours,
            since_iso=since.isoformat(),
        )
