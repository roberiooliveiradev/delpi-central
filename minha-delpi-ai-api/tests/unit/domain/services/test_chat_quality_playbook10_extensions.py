from app.domain.services.chat_feedback_content_service import ChatFeedbackContentService
from app.domain.services.chat_feedback_issue_service import ChatFeedbackIssueService
from app.domain.services.chat_quality_unified_metrics_service import (
    ChatQualityUnifiedMetricsService,
)
from app.domain.services.chat_weekly_quality_report_service import ChatWeeklyQualityReportService


def test_public_feedback_reasons_payload_matches_playbook():
    payload = ChatFeedbackContentService.public_payload()

    assert len(payload["reasons"]) >= 5
    assert "lost_context" in payload["primaryReasonIds"]
    assert payload["downPrompt"]


def test_unified_metrics_builds_health_sections():
    summary = ChatQualityUnifiedMetricsService.build(
        feedback={"csat": 0.8, "totalFeedback": 10, "negativeCount": 2, "alerts": []},
        metrics={"errorRate24h": 0.1, "advanced": {"latencyAvgMs": 900}},
        security={"blockedCount": 1},
        adoption={"activeUsers": 3, "messagesSent": 20, "activeSessions": 4},
        hours=168,
        since_iso="2026-05-25T00:00:00Z",
    )

    assert summary["health"]["csat"] == 0.8
    assert summary["adoption"]["activeUsers"] == 3
    assert summary["security"]["blockedCount"] == 1


def test_weekly_report_markdown_contains_sections():
    from datetime import datetime, timezone

    markdown = ChatWeeklyQualityReportService.build_markdown(
        summary={
            "feedback": {
                "total": 5,
                "positive": 3,
                "negative": 2,
                "topReasons": [],
                "topIntents": [],
                "alerts": [],
            },
            "adoption": {"activeUsers": 2},
            "efficiency": {},
            "security": {},
            "health": {"csat": 0.6, "lostContextCount": 1},
        },
        period_start=datetime(2026, 5, 25, tzinfo=timezone.utc),
        period_end=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )

    assert "Relatório Semanal" in markdown
    assert "Adoção" in markdown
    assert "Segurança" in markdown


def test_issue_service_skips_duplicate_open_issue():
    class FakeIssueRepository:
        def find_open_by_code(self, code, *, within_days=7):
            return {"id": 1, "code": code}

        def create(self, **kwargs):
            return {"id": 99}

    ChatFeedbackIssueService.configure(FakeIssueRepository())

    created = ChatFeedbackIssueService.evaluate_alerts(
        [{"code": "context_loss", "message": "Perda de contexto"}],
    )

    assert created == []
