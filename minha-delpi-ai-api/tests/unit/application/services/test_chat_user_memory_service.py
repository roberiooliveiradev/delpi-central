import contextlib

from app.application.services.chat_user_memory_service import ChatUserMemoryService
from app.infrastructure.config.settings import Settings


class _FakeRepo:
    def __init__(self, *, duplicate=None, active_items=None):
        self.duplicate = duplicate
        self.active_items = active_items or []
        self.created = []
        self.bumped = []

    def find_active_duplicate(self, **kwargs):
        return self.duplicate

    def create(self, **kwargs):
        self.created.append(kwargs)
        return {"id": 1, **kwargs}

    def bump_evidence(self, item_id, **kwargs):
        self.bumped.append(item_id)
        return {"id": item_id, **kwargs}

    def list_active_for_context(self, **kwargs):
        return self.active_items


@contextlib.contextmanager
def _fake_savepoint():
    yield


def _patch_db(monkeypatch):
    from app.extensions import db as db_module

    class _FakeSession:
        def begin_nested(self):
            return _fake_savepoint()

    monkeypatch.setattr(db_module.db, "session", _FakeSession(), raising=False)


def test_capture_disabled_by_flag(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", False, raising=False)
    repo = _FakeRepo()
    service = ChatUserMemoryService(repository=repo)

    result = service.capture_from_turn(message="Sempre responda em português", user_id="u1")

    assert result is None
    assert repo.created == []


def test_capture_requires_user(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_CAPTURE", True, raising=False)
    repo = _FakeRepo()
    service = ChatUserMemoryService(repository=repo)

    assert service.capture_from_turn(message="Sempre responda em português", user_id=None) is None


def test_capture_creates_item(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_CAPTURE", True, raising=False)
    _patch_db(monkeypatch)

    repo = _FakeRepo()
    service = ChatUserMemoryService(repository=repo)

    result = service.capture_from_turn(
        message="De agora em diante responda sempre de forma resumida",
        user_id="11111111-1111-1111-1111-111111111111",
    )

    assert result is not None
    assert len(repo.created) == 1
    assert repo.created[0]["type"] == "preference"


def test_capture_bumps_existing(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_CAPTURE", True, raising=False)
    _patch_db(monkeypatch)

    repo = _FakeRepo(duplicate={"id": 7})
    service = ChatUserMemoryService(repository=repo)

    service.capture_from_turn(
        message="Sempre responda em português",
        user_id="11111111-1111-1111-1111-111111111111",
    )

    assert repo.bumped == [7]
    assert repo.created == []


def test_capture_blocks_sensitive(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_CAPTURE", True, raising=False)
    _patch_db(monkeypatch)

    repo = _FakeRepo()
    service = ChatUserMemoryService(repository=repo)

    # contém e-mail (PII) -> bloqueado pelo safety guard
    result = service.capture_from_turn(
        message="pode me chamar de contato@empresa.com",
        user_id="11111111-1111-1111-1111-111111111111",
    )

    assert result is None
    assert repo.created == []


def test_format_prompt_block_gated(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", False, raising=False)
    service = ChatUserMemoryService(repository=_FakeRepo())

    assert service.format_prompt_block_for(user_id="u1") == ""


def test_format_prompt_block_renders_items(monkeypatch):
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_ENABLED", True, raising=False)
    monkeypatch.setattr(Settings, "CHAT_USER_MEMORY_APPLY", True, raising=False)

    repo = _FakeRepo(
        active_items=[
            {"type": "preference", "content": "Responda sempre de forma resumida"},
            {"type": "profile", "content": "Pode me chamar de João"},
        ]
    )
    service = ChatUserMemoryService(repository=repo)

    block = service.format_prompt_block_for(
        user_id="11111111-1111-1111-1111-111111111111"
    )

    assert "Memória persistente do usuário" in block
    assert "Responda sempre de forma resumida" in block
    assert "[Perfil]" in block


def test_build_prompt_block_empty():
    assert ChatUserMemoryService.build_prompt_block([]) == ""
