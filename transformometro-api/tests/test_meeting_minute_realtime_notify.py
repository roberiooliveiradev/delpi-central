"""Realtime invalidation for meeting minutes (Portal + TÉO + public sign)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from tm_app.application.services.meeting_minute_conflict import MeetingMinuteConflictError
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.application.services.transformometro_realtime_notify import (
    _related_rooms,
    infer_section_key,
)
from tests.test_meeting_minutes_service import FakeRepo

MINUTE_ID = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
USER = SimpleNamespace(
    id="11111111-1111-1111-1111-111111111111",
    is_superadmin=True,
    permissions=[],
)


def test_section_key_and_catalog_fanout_for_meeting_minute():
    assert infer_section_key("meeting_minute", "create") == "meeting_minute"
    assert infer_section_key("meeting_minute", "signers.updated") == "signers"
    assert infer_section_key("meeting_minute", "signature.registered") == "status"
    rooms = _related_rooms(
        "meeting_minute",
        MINUTE_ID,
        {"status": "draft", "unit_code": "01"},
    )
    assert f"meeting_minute:{MINUTE_ID}" in rooms
    assert "catalog:meeting_minute" in rooms


def test_create_emits_realtime_without_sensitive_payload():
    repo = FakeRepo()
    repo.minute = None
    service = MeetingMinutesService(repo)
    service.notifications = SimpleNamespace(
        notify_sign_pending=lambda **_: True,
        notify_minute_signed=lambda **_: True,
        notify_minute_refused=lambda **_: True,
    )
    with patch(
        "tm_app.application.services.meeting_minutes_service.notify_entity_updated"
    ) as notify:
        service.create(
            USER,
            {
                "unit_code": "01",
                "title": "Realtime",
                "meeting_date": "2026-11-09",
                "agenda_html": "<p>secreto</p>",
                "body_html": "<p>corpo</p>",
                "participants": [
                    {
                        "user_id": USER.id,
                        "display_name": "Ana",
                        "must_sign": True,
                    }
                ],
            },
        )
        assert notify.called
        kwargs = notify.call_args.kwargs
        assert kwargs["entity_type"] == "meeting_minute"
        assert kwargs["action"] == "create"
        payload = kwargs["payload"]
        blob = str(payload)
        assert "secreto" not in blob
        assert "corpo" not in blob
        assert "agenda_html" not in payload
        assert "raw_token" not in payload


def test_update_requires_expected_updated_at_and_conflicts():
    repo = FakeRepo()
    service = MeetingMinutesService(repo)
    service.create(
        USER,
        {
            "unit_code": "01",
            "title": "Concurrency",
            "meeting_date": "2026-11-09",
            "participants": [
                {
                    "user_id": USER.id,
                    "display_name": "Ana",
                    "must_sign": True,
                }
            ],
        },
    )
    with pytest.raises(ValueError, match="expected_updated_at"):
        service.update(USER, "m1", {"title": "Sem revisão"})

    with patch(
        "tm_app.application.services.meeting_minutes_service.notify_entity_updated"
    ) as notify:
        detail = service.update(
            USER,
            "m1",
            {
                "title": "Com revisão",
                "expected_updated_at": repo.minute["updated_at"],
            },
        )
        assert detail["minute"]["title"] == "Com revisão"
        assert notify.called

    with pytest.raises(MeetingMinuteConflictError):
        service.update(
            USER,
            "m1",
            {
                "title": "Stale",
                "expected_updated_at": "2020-01-01T00:00:00+00:00",
            },
        )


def test_soft_delete_emits_delete_action():
    repo = FakeRepo()
    service = MeetingMinutesService(repo)
    service.create(
        USER,
        {
            "unit_code": "01",
            "title": "Delete me",
            "meeting_date": "2026-11-09",
            "participants": [
                {
                    "user_id": USER.id,
                    "display_name": "Ana",
                    "must_sign": True,
                }
            ],
        },
    )

    def soft_delete(minute_id, actor_user_id):
        repo.minute = {
            **repo.minute,
            "deleted_at": "2026-11-09T13:00:00+00:00",
            "status": "draft",
        }
        return repo.minute

    repo.soft_delete = soft_delete  # type: ignore[method-assign]
    with patch(
        "tm_app.application.services.meeting_minutes_service.notify_entity_updated"
    ) as notify:
        service.soft_delete(USER, "m1")
        assert notify.call_args.kwargs["action"] == "delete"
