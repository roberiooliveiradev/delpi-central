from app.application.use_cases.get_admin_session_memory_summary_use_case import (
    GetAdminSessionMemorySummaryUseCase,
)


class _FakeAuditRepo:
    def get_session_memory_summary(self, *, hours: int = 168) -> dict:
        return {
            "windowHours": hours,
            "since": "2026-06-01T00:00:00Z",
            "memoryTurnsCount": 4,
            "alerts": [],
        }


class _FakeFeedbackRepo:
    def list_feedback_since(self, *, since):
        return [
            {
                "messageId": "m1",
                "rating": -1,
                "reason": "memory_wrong_context",
                "contextMetadata": {"usedMemory": True},
            }
        ]


def test_execute_merges_usage_and_feedback():
    use_case = GetAdminSessionMemorySummaryUseCase(_FakeAuditRepo(), _FakeFeedbackRepo())
    result = use_case.execute(hours=24)

    assert result["memoryTurnsCount"] == 4
    assert result["feedback"]["feedbackTotal"] == 1
    assert result["feedback"]["feedbackByReason"]["memory_wrong_context"] == 1
