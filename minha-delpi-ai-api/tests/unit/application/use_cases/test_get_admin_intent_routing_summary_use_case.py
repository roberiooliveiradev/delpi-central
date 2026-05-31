from app.application.use_cases.get_admin_intent_routing_summary_use_case import (
    GetAdminIntentRoutingSummaryUseCase,
)


class _FakeAuditRepo:
    def get_intent_routing_summary(self, *, hours: int = 168) -> dict:
        return {"windowHours": hours, "routesCount": 2, "byIntent": {"text_task": 1}}


def test_execute_delegates_to_repository():
    use_case = GetAdminIntentRoutingSummaryUseCase(_FakeAuditRepo())

    result = use_case.execute(hours=48)

    assert result["routesCount"] == 2
    assert result["windowHours"] == 48
