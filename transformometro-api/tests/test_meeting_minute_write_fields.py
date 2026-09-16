"""Meeting-minute write field normalization (UI + GPT shared gate)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.services.meeting_minute_write_fields import (
    normalize_minute_create_fields,
    normalize_optional_time,
    normalize_optional_uuid,
    uuid_bind_or_none,
)
from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.core.catalogs import MEETING_MINUTE_TYPES


_ACTOR = "11111111-1111-1111-1111-111111111111"


def test_normalize_create_positive_minimal():
    fields = normalize_minute_create_fields(
        {
            "unit_code": "1",
            "title": "  Ata X  ",
            "meeting_date": "2026-09-16",
        },
        actor_user_id=_ACTOR,
    )
    assert fields["unit_code"] == "01"
    assert fields["title"] == "Ata X"
    assert fields["meeting_type"] == "ordinary"
    assert fields["meeting_date"] == "2026-09-16"
    assert fields["responsible_user_id"] is None
    assert fields["created_by_user_id"] == _ACTOR


def test_empty_responsible_uuid_becomes_none_sibling():
    fields = normalize_minute_create_fields(
        {
            "unit_code": "01",
            "title": "Ata",
            "meeting_date": "2026-09-16",
            "responsible_user_id": "",
            "start_time": "",
        },
        actor_user_id=_ACTOR,
    )
    assert fields["responsible_user_id"] is None
    assert fields["start_time"] is None
    assert uuid_bind_or_none("") is None


def test_br_date_rejected_negative():
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        normalize_minute_create_fields(
            {
                "unit_code": "01",
                "title": "Ata",
                "meeting_date": "16/09/2026",
            },
            actor_user_id=_ACTOR,
        )


def test_pt_meeting_type_rejected_negative():
    with pytest.raises(ValueError, match="meeting_type"):
        normalize_minute_create_fields(
            {
                "unit_code": "01",
                "title": "Ata",
                "meeting_date": "2026-09-16",
                "meeting_type": "ordinaria",
            },
            actor_user_id=_ACTOR,
        )


def test_bad_time_rejected_negative():
    with pytest.raises(ValueError, match="start_time"):
        normalize_optional_time("14h30", field="start_time")


def test_invalid_uuid_string_rejected():
    with pytest.raises(ValueError, match="responsible_user_id"):
        normalize_optional_uuid("not-a-uuid", field="responsible_user_id")


def test_catalog_types_match_v042_check():
    assert set(MEETING_MINUTE_TYPES) == {
        "ordinary",
        "extraordinary",
        "workshop",
        "follow_up",
        "kickoff",
        "other",
    }


def test_service_create_does_not_call_repo_on_bad_date():
    repo = MagicMock()
    service = MeetingMinutesService(repo)
    user = SimpleNamespace(id=_ACTOR, is_superadmin=True, permissions=[])
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        service.create(
            user,
            {
                "unit_code": "01",
                "title": "Ata",
                "meeting_date": "16/09/2026",
            },
        )
    repo.create_minute.assert_not_called()


def test_service_create_blank_responsible_reaches_repo_as_none():
    repo = MagicMock()
    repo.create_minute.return_value = {
        "id": "m1",
        "unit_code": "01",
        "status": "draft",
        "current_version_id": "v1",
        "title": "Ata",
    }
    repo.get_minute.return_value = repo.create_minute.return_value
    repo.get_version.return_value = {"id": "v1"}
    repo.list_participants.return_value = []
    repo.list_signers.return_value = []
    repo.list_signatures.return_value = []
    repo.list_versions.return_value = []
    service = MeetingMinutesService(repo)
    user = SimpleNamespace(id=_ACTOR, is_superadmin=True, permissions=[])
    service.create(
        user,
        {
            "unit_code": "01",
            "title": "Ata",
            "meeting_date": "2026-09-16",
            "responsible_user_id": "",
            "start_time": "14:30",
        },
    )
    kwargs = repo.create_minute.call_args.kwargs
    assert kwargs["responsible_user_id"] is None
    assert kwargs["start_time"] == "14:30"
    assert kwargs["meeting_date"] == "2026-09-16"


def test_gpt_create_meeting_minute_invalid_date_is_400_not_500():
    dispatch = GptActionsDispatchService()
    request = MagicMock()
    request.state.user = SimpleNamespace(id=_ACTOR, permissions=[], is_superadmin=True)
    with pytest.raises(GptActionsError) as exc:
        dispatch.create_record(
            request,
            "meeting_minute",
            {
                "data": {
                    "unit_code": "01",
                    "title": "Ata filial 01",
                    "meeting_date": "16/09/2026",
                }
            },
        )
    assert exc.value.status_code == 400
    assert "YYYY-MM-DD" in exc.value.message


def test_gpt_create_meeting_minute_empty_uuid_succeeds_path():
    dispatch = GptActionsDispatchService()
    request = MagicMock()
    request.state.user = SimpleNamespace(id=_ACTOR, permissions=[], is_superadmin=True)
    detail = {"minute": {"id": "m1", "title": "Ata", "unit_code": "01", "status": "draft"}}
    with patch.object(dispatch, "_minutes") as minutes:
        minutes.create.return_value = detail
        row, message, status = dispatch.create_record(
            request,
            "meeting_minute",
            {
                "data": {
                    "unit_code": "01",
                    "title": "Ata",
                    "meeting_date": "2026-09-16",
                    "responsible_user_id": "",
                }
            },
        )
    assert status == 201
    assert row["minute"]["id"] == "m1"
    assert "criada" in message.lower()
    minutes.create.assert_called_once()
