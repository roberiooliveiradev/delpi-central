from uuid import uuid4

from app.application.services.chat_session_memory_service import ChatSessionMemoryService


class FakeMemoryRepository:
    def __init__(self):
        self.overlay = {
            "lastEntities": {"productCode": "10080001"},
            "behaviorInstructions": {"responseFormat": "table"},
        }
        self.synced: list[dict] = []
        self.cleared = 0

    def load_active_overlay(self, session_id):
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
        self.overlay = {"lastEntities": {}, "behaviorInstructions": {}}
        return 2

    def expire_stale(self, *, older_than_days=30):
        return 0


def test_apply_to_pre_turn_merges_persisted_entities():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    snapshot = service.apply_to_pre_turn(
        session_id=session_id,
        snapshot={"lastEntities": {}, "behaviorInstructions": {}},
        message="mostre fornecedores",
    )

    assert snapshot["lastEntities"]["productCode"] == "10080001"
    assert snapshot["behaviorInstructions"]["responseFormat"] == "table"
    assert snapshot["persistedMemoryApplied"] is True


def test_apply_to_pre_turn_history_wins_over_persisted():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)

    snapshot = service.apply_to_pre_turn(
        session_id=uuid4(),
        snapshot={
            "lastEntities": {"productCode": "90260015"},
            "behaviorInstructions": {},
        },
        message="estoque",
    )

    assert snapshot["lastEntities"]["productCode"] == "90260015"


def test_clear_context_request_deactivates_memory():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    snapshot = service.apply_to_pre_turn(
        session_id=session_id,
        snapshot={"lastEntities": {"productCode": "1"}, "behaviorInstructions": {}},
        message="a partir de agora, desconsidere produto e filial desta conversa.",
    )

    assert repo.cleared == 1
    assert snapshot["lastEntities"] == {}
    assert snapshot["persistedMemoryCleared"] is True


def test_persist_post_turn_skips_after_clear():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)

    service.persist_post_turn(
        session_id=uuid4(),
        snapshot={"persistedMemoryCleared": True, "lastEntities": {"productCode": "1"}},
    )

    assert repo.synced == []


def test_persist_post_turn_syncs_snapshot():
    repo = FakeMemoryRepository()
    service = ChatSessionMemoryService(repo)
    session_id = uuid4()

    service.persist_post_turn(
        session_id=session_id,
        snapshot={
            "lastEntities": {"productCode": "10080001", "branch": "02"},
            "behaviorInstructions": {"tone": "simple"},
        },
        source_message_id=uuid4(),
    )

    assert len(repo.synced) == 1
    assert repo.synced[0]["session_id"] == session_id
