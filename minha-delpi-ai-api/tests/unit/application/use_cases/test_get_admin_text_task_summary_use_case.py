from app.application.use_cases.get_admin_text_task_summary_use_case import (
    GetAdminTextTaskSummaryUseCase,
)


class _FakeAuditRepo:
    def get_text_task_summary(self, *, hours: int = 168) -> dict:
        return {"windowHours": hours, "textTasksCount": 3, "bySubtype": {"text_correct": 2}}


class _FakeFeedbackRepo:
    def list_feedback_since(self, *, since):
        return [
            {
                "messageId": "m1",
                "rating": -1,
                "reason": "text_meaning_changed",
                "contextMetadata": {
                    "intent": "text_task",
                    "textTaskSubtype": "text_correct",
                    "textTaskIntent": "text.correct",
                },
                "createdAt": since.isoformat(),
            },
            {
                "messageId": "m2",
                "rating": 1,
                "reason": None,
                "contextMetadata": {"intent": "sql_task"},
                "createdAt": since.isoformat(),
            },
        ]


def test_execute_merges_usage_and_feedback():
    use_case = GetAdminTextTaskSummaryUseCase(_FakeAuditRepo(), _FakeFeedbackRepo())

    result = use_case.execute(hours=72)

    assert result["textTasksCount"] == 3
    assert result["windowHours"] == 72
    assert result["feedback"]["feedbackNegative"] == 1
    assert result["feedback"]["feedbackByReason"]["text_meaning_changed"] == 1
