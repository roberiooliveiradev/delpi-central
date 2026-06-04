from uuid import uuid4

from app.application.services.chat_session_memory_service import ChatSessionMemoryService


class FakeMemoryRepository:
    def __init__(self):
        self.overlay = {
            "operationalFocus": {"productCode": "10080001"},
            "behaviorInstructions": {"responseFormat": "table"},
        }
        self.synced: list[dict] = []
        self.cleared = 0
        self.clear_marker = False

    def load_active_overlay(self, session_id):
        if self.clear_marker:
            return {"operationalFocus": {}, "behaviorInstructions": {}, "cleared": True}
        return dict(self.overlay)

    def sync_from_snapshot(self, session_id, snapshot, *, source_message_id=None):
        self.synced.append(
            {
                "session_id": session_id,
                "snapshot": snapshot,
                "source_message_id": source_message_id,
            }
        )

    def deactivate_all(self, session_id):
        self.cleared += 1
        self.clear_marker = True
        self.overlay = {"operationalFocus": {}, "behaviorInstructions": {}}
        return 2

    def expire_stale(self, *, older_than_days=30):
        return 0


def test_apply_to_pre_turn_merges_persisted_entities():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    snapshot = service.apply_to_pre_turn(
        session_id=session_id,
        snapshot={"operationalFocus": {}, "behaviorInstructions": {}},
        message="mostre fornecedores",
    )

    assert snapshot["operationalFocus"]["productCode"] == "10080001"
    assert snapshot["behaviorInstructions"]["responseFormat"] == "table"
    assert snapshot["persistedMemoryApplied"] is True


def test_apply_to_pre_turn_history_wins_over_persisted():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)

    snapshot = service.apply_to_pre_turn(
        session_id=uuid4(),
        snapshot={
            "operationalFocus": {"productCode": "90260015"},
            "behaviorInstructions": {},
        },
        message="estoque",
    )

    assert snapshot["operationalFocus"]["productCode"] == "90260015"


def test_clear_context_request_deactivates_memory():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    snapshot = service.apply_to_pre_turn(
        session_id=session_id,
        snapshot={"operationalFocus": {"productCode": "1"}, "behaviorInstructions": {}},
        message="a partir de agora, desconsidere produto e filial desta conversa.",
    )

    assert repo.cleared == 1
    assert snapshot["operationalFocus"] == {}
    assert snapshot["persistedMemoryCleared"] is True


def test_persist_post_turn_skips_after_clear():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)

    service.persist_post_turn(
        session_id=uuid4(),
        snapshot={"persistedMemoryCleared": True, "operationalFocus": {"productCode": "1"}},
    )

    assert repo.synced == []


def test_apply_after_api_clear_zeros_entities():
    repo = FakeMemoryRepository()
    repo.clear_marker = True
    service = ChatSessionMemoryService(repo)

    snapshot = service.apply_to_pre_turn(
        session_id=uuid4(),
        snapshot={
            "operationalFocus": {"productCode": "10080001"},
            "behaviorInstructions": {"tone": "simple"},
        },
        message="mostre fornecedores",
    )

    assert snapshot["operationalFocus"] == {}
    assert snapshot["persistedMemoryCleared"] is True


def test_persist_post_turn_syncs_snapshot():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    service.persist_post_turn(
        session_id=session_id,
        snapshot={
            "operationalFocus": {"productCode": "10080001", "branch": "02"},
            "behaviorInstructions": {"tone": "simple"},
        },
        source_message_id=uuid4(),
    )

    assert len(repo.synced) == 1
    assert repo.synced[0]["session_id"] == session_id


def test_persist_post_turn_syncs_email_writing_preference():
    import json

    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    service.persist_post_turn(
        session_id=session_id,
        snapshot={
            "operationalFocus": {},
            "behaviorInstructions": {
                "emailWriting": json.dumps({"shortEmails": True, "formalTone": True}),
                "scope": "session",
            },
        },
    )

    assert len(repo.synced) == 1
    assert "emailWriting" in repo.synced[0]["snapshot"]["behaviorInstructions"]
