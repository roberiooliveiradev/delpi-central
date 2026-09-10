from app.application.use_cases.get_admin_registry_selection_shadow_summary_use_case import (
    GetAdminRegistrySelectionShadowSummaryUseCase,
)


class _FakeAuditRepo:
    def get_registry_selection_shadow_summary(self, *, hours: int = 168) -> dict:
        return {
            "windowHours": hours,
            "samplesCount": 3,
            "agreeCount": 2,
            "agreeRate": 0.6667,
        }


def test_execute_delegates_to_repository():
    use_case = GetAdminRegistrySelectionShadowSummaryUseCase(_FakeAuditRepo())
    result = use_case.execute(hours=48)
    assert result["samplesCount"] == 3
    assert result["windowHours"] == 48
