from app.application.use_cases.get_admin_sql_advanced_summary_use_case import (
    GetAdminSqlAdvancedSummaryUseCase,
)


class FakeAuditRepository:
    def get_sql_advanced_summary(self, *, hours: int = 168) -> dict:
        return {"windowHours": hours, "runsCount": 2}


def test_get_admin_sql_advanced_summary_use_case():
    use_case = GetAdminSqlAdvancedSummaryUseCase(FakeAuditRepository())

    result = use_case.execute(hours=24)

    assert result["windowHours"] == 24
    assert result["runsCount"] == 2
