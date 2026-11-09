"""Draft-only soft-delete policy for meeting minutes."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tm_app.application.services.meeting_minutes_service import MeetingMinutesService
from tm_app.domain.services.minute_status_transition_service import (
    MinuteStatusTransitionError,
    MinuteStatusTransitionService,
)


def test_assert_soft_deletable_allows_clean_draft() -> None:
    MinuteStatusTransitionService.assert_soft_deletable(
        {"status": "draft", "submitted_for_signature_at": None},
        completed_signature_count=0,
    )


@pytest.mark.parametrize(
    "status",
    [
        "in_review",
        "awaiting_signatures",
        "partially_signed",
        "signed",
        "finalized",
        "cancelled",
    ],
)
def test_assert_soft_deletable_blocks_non_draft(status: str) -> None:
    with pytest.raises(MinuteStatusTransitionError):
        MinuteStatusTransitionService.assert_soft_deletable(
            {"status": status, "submitted_for_signature_at": None},
            completed_signature_count=0,
        )


def test_assert_soft_deletable_blocks_submitted_even_if_draft() -> None:
    with pytest.raises(MinuteStatusTransitionError):
        MinuteStatusTransitionService.assert_soft_deletable(
            {
                "status": "draft",
                "submitted_for_signature_at": "2026-11-09T12:00:00Z",
            },
            completed_signature_count=0,
        )


def test_assert_soft_deletable_blocks_when_signatures_exist() -> None:
    with pytest.raises(MinuteStatusTransitionError):
        MinuteStatusTransitionService.assert_soft_deletable(
            {"status": "draft", "submitted_for_signature_at": None},
            completed_signature_count=1,
        )


class _DeleteRepo:
    def __init__(self, minute: dict, signatures: list | None = None) -> None:
        self.minute = minute
        self.signatures = list(signatures or [])
        self.deleted = False
        self.soft_delete_calls = 0

    def get_minute(self, _):
        return None if self.deleted else dict(self.minute)

    def list_signatures(self, _):
        return list(self.signatures)

    def soft_delete(self, minute_id, actor_user_id):
        self.soft_delete_calls += 1
        # Mirror commit-time gate used by the real repository.
        MinuteStatusTransitionService.assert_soft_deletable(
            self.minute,
            completed_signature_count=len(self.signatures),
        )
        self.deleted = True
        out = {**self.minute, "id": minute_id, "deleted_at": "now"}
        self.minute = out
        return out


def _user():
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        permissions=["transformometro.access"],
    )


def test_service_soft_delete_draft_ok(monkeypatch) -> None:
    repo = _DeleteRepo(
        {
            "id": "m1",
            "status": "draft",
            "unit_code": "01",
            "submitted_for_signature_at": None,
        }
    )
    svc = MeetingMinutesService()
    svc.repo = repo
    monkeypatch.setattr(svc._authz, "has_access", lambda _u: True)
    result = svc.soft_delete(_user(), "m1")
    assert result["minute"]["deleted_at"] == "now"
    assert repo.soft_delete_calls == 1


def test_service_soft_delete_blocks_awaiting(monkeypatch) -> None:
    repo = _DeleteRepo(
        {
            "id": "m1",
            "status": "awaiting_signatures",
            "unit_code": "01",
            "submitted_for_signature_at": "2026-11-01T00:00:00Z",
        }
    )
    svc = MeetingMinutesService()
    svc.repo = repo
    monkeypatch.setattr(svc._authz, "has_access", lambda _u: True)
    with pytest.raises(ValueError, match="rascunho"):
        svc.soft_delete(_user(), "m1")
    assert repo.soft_delete_calls == 0


def test_service_soft_delete_blocks_with_signatures(monkeypatch) -> None:
    repo = _DeleteRepo(
        {
            "id": "m1",
            "status": "draft",
            "unit_code": "01",
            "submitted_for_signature_at": None,
        },
        signatures=[{"id": "sig1"}],
    )
    svc = MeetingMinutesService()
    svc.repo = repo
    monkeypatch.setattr(svc._authz, "has_access", lambda _u: True)
    with pytest.raises(ValueError, match="assinatura"):
        svc.soft_delete(_user(), "m1")
    assert repo.soft_delete_calls == 0


def test_can_delete_status_set_is_draft_only() -> None:
    assert MinuteStatusTransitionService.can_delete("draft") is True
    assert MinuteStatusTransitionService.can_delete("awaiting_signatures") is False
    assert MinuteStatusTransitionService.can_delete("partially_signed") is False
