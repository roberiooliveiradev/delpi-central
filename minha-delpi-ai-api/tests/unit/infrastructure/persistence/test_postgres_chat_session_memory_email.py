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
