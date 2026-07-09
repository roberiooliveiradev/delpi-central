import json
from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import UUID

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
            "heartbeat_at": datetime(2026, 7, 9, 18, 0, tzinfo=timezone.utc),
            "lock_expires_at": datetime(2026, 7, 9, 18, 2, tzinfo=timezone.utc),
        }
    ]
    service = CollaborationPresenceService(repo=repo)

    payload = service.list_presence(entity_type="processo", entity_id="00000000-0000-0000-0000-000000000001")

    json.dumps(payload)
    assert payload["editors"][0]["heartbeat_at"] == "2026-07-09T18:00:00+00:00"
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
