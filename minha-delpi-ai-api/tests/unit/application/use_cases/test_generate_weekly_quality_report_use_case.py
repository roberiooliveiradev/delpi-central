from datetime import datetime, timezone
from unittest.mock import Mock

from app.application.use_cases.generate_weekly_quality_report_use_case import (
    GenerateWeeklyQualityReportUseCase,
)
from app.domain.ports.chat_quality_report_repository_port import ChatQualityReportRepositoryPort


class _FakeReportRepository(ChatQualityReportRepositoryPort):
    def __init__(self):
        self.last_create: dict | None = None

    def create(
        self,
        *,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        summary_json: dict,
        markdown: str,
    ) -> dict:
        self.last_create = {
            "report_type": report_type,
            "period_start": period_start,
            "period_end": period_end,
            "summary_json": summary_json,
            "markdown": markdown,
        }
        return {
            "id": 42,
            "reportType": report_type,
            "periodStart": period_start.isoformat(),
            "periodEnd": period_end.isoformat(),
            "summary": summary_json,
            "markdown": markdown,
            "createdAt": datetime.now(timezone.utc).isoformat(),
        }

    def get_latest(self, *, report_type: str = "weekly") -> dict | None:
        return None

    def list_recent(self, *, report_type: str = "weekly", limit: int = 12) -> list[dict]:
        return []


def test_generate_weekly_quality_report_persists_via_port():
    repository = _FakeReportRepository()
    summary_use_case = Mock()
    summary_use_case.execute.return_value = {
        "feedback": {"alerts": [], "total": 0},
        "health": {"csat": 0.9},
    }

    use_case = GenerateWeeklyQualityReportUseCase(
        report_repository=repository,
        summary_use_case=summary_use_case,
    )

    result = use_case.execute(create_issues=False)

    assert repository.last_create is not None
    assert repository.last_create["report_type"] == "weekly"
    assert "Relatório" in repository.last_create["markdown"] or len(repository.last_create["markdown"]) > 0
    assert result["report"]["id"] == 42
    assert result["issuesCreated"] == []
    summary_use_case.execute.assert_called_once_with(hours=168)
