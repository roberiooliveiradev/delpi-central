from app.application.services.chat_evaluation_case_service import ChatEvaluationCaseService
from app.infrastructure.config.settings import Settings


class _FakeRepo:
    def __init__(self):
        self.created = []
        self.cases = []

    def create(self, **kwargs):
        row = {"id": len(self.created) + 1, **kwargs, "status": "active"}
        self.created.append(row)
        return {
            "id": row["id"],
            "category": kwargs.get("category"),
            "input": kwargs.get("input_text"),
            "expectedIntent": kwargs.get("expected_intent"),
            "expectedNormalized": kwargs.get("expected_normalized"),
            "mustNotUseTools": kwargs.get("must_not_use_tools"),
            "mustNotUseRag": kwargs.get("must_not_use_rag"),
            "status": "active",
        }

    def get(self, case_id):
        for item in self.created:
            if item["id"] == case_id:
                return {
                    "id": case_id,
                    "input": item.get("input_text") or item.get("input"),
                    "expectedIntent": item.get("expected_intent"),
                    "category": item.get("category"),
                }
        return None

    def list_active(self, *, categories=None):
        return [
            {
                "id": 1,
                "input": "como vc s chama?",
                "expectedIntent": "assistant_identity",
                "mustNotUseTools": True,
                "mustNotUseRag": True,
            }
        ]

    def update_run_result(self, case_id, *, passed, failure_reason=None):
        return {"id": case_id, "lastPassed": passed}

    def find_duplicate_input(self, **kwargs):
        return None


def test_run_all_active(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_LEARNING_EVALUATION_ENABLED", True, raising=False)

    repo = _FakeRepo()
    service = ChatEvaluationCaseService(repository=repo)
    summary = service.run_all_active()

    assert summary["enabled"] is True
    assert summary["passed"] >= 1
