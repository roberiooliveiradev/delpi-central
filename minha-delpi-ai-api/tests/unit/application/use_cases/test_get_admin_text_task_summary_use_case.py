from app.application.use_cases.get_admin_text_task_summary_use_case import (
    GetAdminTextTaskSummaryUseCase,
)


class _FakeAuditRepo:
    def get_text_task_summary(self, *, hours: int = 168) -> dict:
        return {"windowHours": hours, "textTasksCount": 3, "bySubtype": {"text_correct": 2}}


def test_execute_delegates_to_repository():
    use_case = GetAdminTextTaskSummaryUseCase(_FakeAuditRepo())

    result = use_case.execute(hours=72)

    assert result["textTasksCount"] == 3
    assert result["windowHours"] == 72
