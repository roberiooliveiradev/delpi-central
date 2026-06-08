from __future__ import annotations

from typing import TYPE_CHECKING

from app.domain.ports.chat_quality_report_repository_port import ChatQualityReportRepositoryPort
from app.domain.services.chat_feedback_issue_service import ChatFeedbackIssueService
from app.domain.services.chat_weekly_quality_report_service import ChatWeeklyQualityReportService

if TYPE_CHECKING:
    from app.application.use_cases.get_admin_quality_unified_summary_use_case import (
        GetAdminQualityUnifiedSummaryUseCase,
    )


def _default_report_repository() -> ChatQualityReportRepositoryPort:
    from app.composition.repository_composer import make_chat_quality_report_repository

    return make_chat_quality_report_repository()


class GenerateWeeklyQualityReportUseCase:
    def __init__(
        self,
        report_repository: ChatQualityReportRepositoryPort | None = None,
        summary_use_case: GetAdminQualityUnifiedSummaryUseCase | None = None,
    ):
        self.report_repository = report_repository or _default_report_repository()
        self._summary_use_case = summary_use_case

    def _resolve_summary_use_case(self) -> GetAdminQualityUnifiedSummaryUseCase:
        if self._summary_use_case is None:
            from app.application.use_cases.get_admin_quality_unified_summary_use_case import (
                GetAdminQualityUnifiedSummaryUseCase,
            )

            self._summary_use_case = GetAdminQualityUnifiedSummaryUseCase()

        return self._summary_use_case

    def execute(self, *, create_issues: bool = True) -> dict:
        period_start, period_end = ChatWeeklyQualityReportService.default_period()
        summary = self._resolve_summary_use_case().execute(hours=168)
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
