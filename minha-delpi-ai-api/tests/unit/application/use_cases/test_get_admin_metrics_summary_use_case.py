from app.application.use_cases.get_admin_metrics_summary_use_case import (
    GetAdminMetricsSummaryUseCase,
)


class FakeAdminMetricsRepository:
    def get_summary(self):
        return {
            "sessions": 1,
            "messages": 2,
            "knowledgeDocuments": 3,
            "activeKnowledgeDocuments": 2,
            "knowledgeChunks": 4,
            "auditLogs": 5,
            "recentToolCalls24h": 6,
            "recentErrors24h": 0,
        }


def test_get_admin_metrics_summary():
    use_case = GetAdminMetricsSummaryUseCase(FakeAdminMetricsRepository())

    result = use_case.execute()

    assert result["sessions"] == 1
    assert result["messages"] == 2
    assert result["recentErrors24h"] == 0
