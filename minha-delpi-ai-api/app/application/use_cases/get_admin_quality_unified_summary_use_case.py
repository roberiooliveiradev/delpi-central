from datetime import datetime, timedelta, timezone

from app.application.services.chat_intelligence_settings_service import (
    ChatIntelligenceSettingsService,
)
from app.application.use_cases.admin_security_use_cases import GetAdminSecuritySummaryUseCase
from app.application.use_cases.get_admin_feedback_summary_use_case import (
    GetAdminFeedbackSummaryUseCase,
)
from app.application.use_cases.get_admin_metrics_summary_use_case import (
    GetAdminMetricsSummaryUseCase,
)
from app.application.use_cases.get_admin_presentation_coverage_use_case import (
    GetAdminPresentationCoverageUseCase,
)
from app.application.use_cases.get_admin_presentation_summary_use_case import (
    GetAdminPresentationSummaryUseCase,
)
from app.application.use_cases.get_admin_session_memory_summary_use_case import (
    GetAdminSessionMemorySummaryUseCase,
)
from app.domain.services.chat_quality_adoption_metrics_service import (
    ChatQualityAdoptionMetricsService,
)
from app.domain.services.chat_quality_unified_metrics_service import (
    ChatQualityUnifiedMetricsService,
)
from app.infrastructure.config.settings import Settings
from app.infrastructure.persistence.postgres_audit_repository import PostgresAuditRepository


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
        presentation = GetAdminPresentationSummaryUseCase(
            PostgresAuditRepository(),
        ).execute(hours=safe_hours)
        presentation_coverage = GetAdminPresentationCoverageUseCase().execute()
        session_memory = GetAdminSessionMemorySummaryUseCase(
            PostgresAuditRepository(),
        ).execute(hours=safe_hours)
        rag_settings = ChatIntelligenceSettingsService().to_dict()

        return ChatQualityUnifiedMetricsService.build(
            feedback=feedback,
            metrics=metrics,
            security=security,
            adoption=adoption,
            presentation=presentation,
            presentation_coverage=presentation_coverage,
            session_memory=session_memory,
            rag_settings=rag_settings,
            hours=safe_hours,
            since_iso=since.isoformat(),
        )
