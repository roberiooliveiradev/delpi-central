from app.application.use_cases.get_admin_drawing_analysis_summary_use_case import (
    GetAdminDrawingAnalysisSummaryUseCase,
)


class FakeAuditRepository:
    def get_drawing_analysis_summary(self, *, hours: int = 168) -> dict:
        return {
            "windowHours": hours,
            "since": "2026-05-24T00:00:00+00:00",
            "analysesCount": 3,
            "uniqueProductCodes": 2,
            "byStatus": {"rejected": 1, "approved": 2},
            "totalCriticalErrors": 1,
            "totalErrors": 0,
            "reportExportedCount": 2,
            "analyserOkCount": 2,
            "withPdfCount": 1,
            "recent": [],
        }


def test_execute_caps_hours_and_returns_summary():
    use_case = GetAdminDrawingAnalysisSummaryUseCase(FakeAuditRepository())

    result = use_case.execute(hours=24)

    assert result["windowHours"] == 24
    assert result["analysesCount"] == 3
    assert result["byStatus"]["approved"] == 2
