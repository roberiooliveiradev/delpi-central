from app.application.services.chat_fine_tuning_service import ChatFineTuningService
from app.infrastructure.config.settings import Settings


class _FakeRepo:
    def __init__(self):
        self.samples = []
        self.datasets = []
        self.runs = []

    def find_sample_by_source(self, **kwargs):
        return None

    def create_sample(self, **kwargs):
        row = {"id": len(self.samples) + 1, "status": "captured", **kwargs}
        row["messages"] = kwargs.get("messages_json")
        row["messagesJson"] = kwargs.get("messages_json")
        self.samples.append(row)
        return {
            "id": row["id"],
            "status": "captured",
            "messages": kwargs.get("messages_json"),
            "category": kwargs.get("category"),
            "intentLabel": kwargs.get("intent_label"),
        }

    def update_sample_status(self, sample_id, **kwargs):
        for sample in self.samples:
            if sample["id"] == sample_id:
                sample["status"] = kwargs.get("status")
                return {"id": sample_id, "status": sample["status"], "messages": sample.get("messages")}
        return None

    def create_dataset(self, **kwargs):
        row = {"id": 1, "status": "draft", "targetModel": kwargs.get("target_model", "intent_classifier")}
        self.datasets.append(row)
        return row

    def get_dataset(self, dataset_id):
        return next((d for d in self.datasets if d["id"] == dataset_id), None)

    def list_approved_for_dataset(self, dataset_id):
        return [
            {
                "id": 1,
                "status": "approved",
                "messages": [{"role": "user", "content": "a"}, {"role": "assistant", "content": "b"}],
                "category": "routing",
            }
            for _ in range(3)
        ]

    def approve_dataset(self, dataset_id, **kwargs):
        dataset = self.get_dataset(dataset_id)
        if dataset:
            dataset["status"] = "approved"
        return dataset

    def create_run(self, **kwargs):
        run = {"id": 1, "datasetId": kwargs["dataset_id"], "status": "pending", "targetModel": kwargs["target_model"]}
        self.runs.append(run)
        return run

    def get_run(self, run_id):
        return self.runs[0] if self.runs else None

    def update_run(self, run_id, **kwargs):
        run = self.get_run(run_id)
        if run:
            run.update({k if k != "export_stats" else "exportStats": v for k, v in kwargs.items()})
        return run

    def deactivate_deploys(self, **kwargs):
        pass


class _FakeFeedbackRepo:
    def get_user_question_for_assistant(self, message_id):
        return "como vc s chama"

    def get_assistant_message(self, message_id):
        class _Msg:
            content = "Sou o assistente Minha DELPI."

        return _Msg()


def test_export_dataset_jsonl(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_FINE_TUNING_ENABLED", True, raising=False)
    service = ChatFineTuningService(repository=_FakeRepo())
    dataset = service.create_dataset(payload={"name": "teste"})
    result = service.export_dataset(dataset["id"])
    assert result["stats"]["lineCount"] >= 3
    assert "messages" in result["jsonl"]


def test_review_sample_approve(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_LEARNING_FINE_TUNING_ENABLED", True, raising=False)
    repo = _FakeRepo()
    service = ChatFineTuningService(repository=repo)
    sample = service.create_sample_manual(
        payload={
            "messages": [
                {"role": "user", "content": "ola"},
                {"role": "assistant", "content": "oi"},
            ]
        }
    )
    reviewed = service.review_sample(sample["id"], action="approve")
    assert reviewed["sample"]["status"] == "approved"
