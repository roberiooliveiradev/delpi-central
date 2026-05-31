from app.application.use_cases.get_admin_document_vision_summary_use_case import (
    GetAdminDocumentVisionSummaryUseCase,
)


class FakeAuditRepository:
    def get_document_vision_summary(self, *, hours: int = 168) -> dict:
        return {"runsCount": 1, "windowHours": hours}


def test_execute_clamps_hours():
    use_case = GetAdminDocumentVisionSummaryUseCase(FakeAuditRepository())
    result = use_case.execute(hours=99999)

    assert result["runsCount"] == 1
    assert result["windowHours"] <= 720
