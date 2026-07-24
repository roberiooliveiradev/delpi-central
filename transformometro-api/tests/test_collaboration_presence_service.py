import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

import pytest

from tm_app.application.services.collaboration_presence_service import CollaborationPresenceService


def test_list_presence_serializes_datetime_for_json():
    repo = MagicMock()
    repo.purge_stale.return_value = None
    repo.list_active.return_value = [
        {
            "user_id": "u1",
            "user_name": "Ana",
            "user_email": "ana@example.com",
            "section_key": "diagrama_macro",
            "mode": "editing",
            "heartbeat_at": datetime(2099, 1, 1, 18, 0, tzinfo=timezone.utc),
            "lock_expires_at": datetime(2099, 1, 1, 18, 2, tzinfo=timezone.utc),
        }
    ]
    service = CollaborationPresenceService(repo=repo)

    payload = service.list_presence(entity_type="processo", entity_id="00000000-0000-0000-0000-000000000001")

    json.dumps(payload)
    assert payload["editors"][0]["heartbeat_at"] == "2099-01-01T18:00:00+00:00"
    assert payload["editors"][0]["lock_active"] is True


def test_serialize_row_converts_uuid_values():
    service = CollaborationPresenceService()
    row = {
        "user_id": UUID("00000000-0000-0000-0000-000000000099"),
        "user_name": None,
        "user_email": "dev@example.com",
        "section_key": "",
        "mode": "viewing",
        "heartbeat_at": datetime(2026, 7, 9, 18, 0, tzinfo=timezone.utc),
        "lock_expires_at": None,
    }

    serialized = service._serialize_row(row)

    json.dumps(serialized)
    assert serialized["user_id"] == "00000000-0000-0000-0000-000000000099"
    assert serialized["heartbeat_at"] == "2026-07-09T18:00:00+00:00"


def test_catalog_rooms_skip_db_presence():
    """Salas catalog:<id> usam entity_id textual; coluna DB é UUID — sem persistência."""
    repo = MagicMock()
    service = CollaborationPresenceService(repo=repo)

    payload = service.list_presence(entity_type="catalog", entity_id="dashboard")
    assert payload == {
        "entity_type": "catalog",
        "entity_id": "dashboard",
        "viewers": [],
        "editors": [],
    }
    repo.list_active.assert_not_called()

    service.clear_user_presence(
        entity_type="catalog",
        entity_id="processo",
        user_id="u1",
    )
    repo.release_user_locks.assert_not_called()
    repo.delete_user_presence.assert_not_called()

    heartbeat = service.heartbeat(
        entity_type="catalog",
        entity_id="dashboard",
        section_key="",
        user_id="u1",
        user_name="Ana",
        user_email="ana@example.com",
    )
    assert heartbeat["mode"] == "viewing"
    repo.upsert_presence.assert_not_called()


def test_non_uuid_entity_id_skips_db_presence():
    repo = MagicMock()
    service = CollaborationPresenceService(repo=repo)

    service.clear_user_presence(
        entity_type="processo",
        entity_id="not-a-uuid",
        user_id="u1",
    )
    repo.release_user_locks.assert_not_called()
    repo.delete_user_presence.assert_not_called()


def test_catalog_acquire_lock_rejected():
    service = CollaborationPresenceService(repo=MagicMock())
    with pytest.raises(ValueError, match="catálogo"):
        service.acquire_lock(
            entity_type="catalog",
            entity_id="dashboard",
            section_key="",
            user_id="u1",
            user_name="Ana",
            user_email=None,
        )
