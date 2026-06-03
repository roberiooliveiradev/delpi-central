from app.domain.services.chat_text_task_admin_metrics_service import (
    ChatTextTaskAdminMetricsService,
)


def test_aggregate_feedback_filters_text_rows():
    rows = [
        {
            "rating": -1,
            "reason": "text_artificial",
            "contextMetadata": {"textTaskSubtype": "text_email_create"},
        },
        {
            "rating": -1,
            "reason": "sql_wrong",
            "contextMetadata": {"intent": "sql_task"},
        },
    ]

    result = ChatTextTaskAdminMetricsService.aggregate_feedback_rows(rows)

    assert result["feedbackNegative"] == 1
    assert result["feedbackByReason"]["text_artificial"] == 1
