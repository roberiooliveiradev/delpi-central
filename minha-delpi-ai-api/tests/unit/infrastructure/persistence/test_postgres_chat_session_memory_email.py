from app.infrastructure.persistence.postgres_chat_session_memory_repository import (
    PostgresChatSessionMemoryRepository,
)


def test_behavior_keys_include_email_writing():
    keys = PostgresChatSessionMemoryRepository._BEHAVIOR_KEYS
    assert "emailWriting" in keys


def test_sync_accepts_email_writing_in_snapshot_filter():
    import json

    behavior = {
        "tone": "direct",
        "emailWriting": json.dumps({"shortEmails": True, "formalTone": True}),
        "scope": "session",
        "ignored": "x",
    }
    allowed = {
        key: value
        for key, value in behavior.items()
        if key in PostgresChatSessionMemoryRepository._BEHAVIOR_KEYS
        and value not in (None, "", [])
    }
    assert "emailWriting" in allowed
    assert "ignored" not in allowed
    assert "scope" in allowed


def test_working_last_action_memory_type_contract():
    """E3.S8: lastAction usa memory_type=working (overlay genérico)."""
    assert hasattr(PostgresChatSessionMemoryRepository, "_deactivate_working_key")
    import inspect

    src = inspect.getsource(PostgresChatSessionMemoryRepository.sync_from_snapshot)
    assert 'memory_type="working"' in src
    assert 'key="lastAction"' in src
    load_src = inspect.getsource(PostgresChatSessionMemoryRepository.load_active_overlay)
    assert 'memory_type == "working"' in load_src
    assert 'key == "lastAction"' in load_src

