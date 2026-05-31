from app.infrastructure.persistence.postgres_chat_session_memory_repository import (
    PostgresChatSessionMemoryRepository,
)


def test_behavior_keys_include_text_correction():
    keys = PostgresChatSessionMemoryRepository._BEHAVIOR_KEYS
    assert "textCorrection" in keys


def test_sync_accepts_text_correction_in_snapshot_filter():
    import json

    behavior = {
        "textCorrection": json.dumps({"deliverFinalOnly": True}),
        "scope": "session",
        "ignored": "x",
    }
    allowed = {
        key: value
        for key, value in behavior.items()
        if key in PostgresChatSessionMemoryRepository._BEHAVIOR_KEYS
        and value not in (None, "", [])
    }
    assert "textCorrection" in allowed
    assert "ignored" not in allowed
