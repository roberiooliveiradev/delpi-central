from app.domain.services.chat_feedback_issue_service import ChatFeedbackIssueService
from app.domain.services.chat_weekly_quality_report_service import ChatWeeklyQualityReportService
from app.application.use_cases.get_admin_quality_unified_summary_use_case import (
    GetAdminQualityUnifiedSummaryUseCase,
)
from app.infrastructure.persistence.postgres_chat_quality_report_repository import (
    PostgresChatQualityReportRepository,
)


class GenerateWeeklyQualityReportUseCase:
    def __init__(
        self,
        report_repository: PostgresChatQualityReportRepository | None = None,
    ):
        self.report_repository = report_repository or PostgresChatQualityReportRepository()

    def execute(self, *, create_issues: bool = True) -> dict:
        period_start, period_end = ChatWeeklyQualityReportService.default_period()
        summary = GetAdminQualityUnifiedSummaryUseCase().execute(hours=168)
        markdown = ChatWeeklyQualityReportService.build_markdown(
            summary=summary,
            period_start=period_start,
            period_end=period_end,
        )

        report = self.report_repository.create(
            report_type="weekly",
            period_start=period_start,
            period_end=period_end,
            summary_json=summary,
            markdown=markdown,
        )

        created_issues: list[dict] = []

        if create_issues:
            alerts = (summary.get("feedback") or {}).get("alerts") or []
            created_issues = ChatFeedbackIssueService.evaluate_alerts(
                alerts,
                source="weekly_report",
                feedback_summary=summary.get("feedback"),
            )

        return {
            "report": report,
            "issuesCreated": created_issues,
        }
