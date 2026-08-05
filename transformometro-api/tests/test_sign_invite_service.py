from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from tm_app.application.services.tm_meeting_minute_sign_invite_service import (
    TmMeetingMinuteSignInviteService,
)
from tm_app.application.services.token_service import hash_token


class _FakeInviteRepo:
    def __init__(self) -> None:
        self.invites: dict[str, dict[str, Any]] = {}
        self.signers: dict[str, dict[str, Any]] = {
            "s1": {
                "id": "s1",
                "status": "pending",
                "unit_code": "01",
                "display_name": "Ana",
            }
        }
        self.minutes: dict[str, dict[str, Any]] = {
            "m1": {
                "id": "m1",
                "unit_code": "01",
                "status": "awaiting_signatures",
                "deleted_at": None,
                "title": "Ata",
            }
        }
        self.invalidated = 0

    def invalidate_open_invites(self, *, signer_id: str) -> int:
        self.invalidated += 1
        return 1

    def create_invite(self, **kwargs: Any) -> dict[str, Any]:
        row = {
            "id": "inv-1",
            "consumed_at": None,
            **kwargs,
        }
        self.invites[kwargs["token_hash"]] = row
        return row

    def get_invite_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        return self.invites.get(token_hash)

    def consume_invite(self, invite_id: str) -> dict[str, Any] | None:
        for row in self.invites.values():
            if row["id"] == invite_id:
                row["consumed_at"] = datetime.now(timezone.utc)
                return row
        return None

    def get_signer(self, signer_id: str) -> dict[str, Any] | None:
        return self.signers.get(signer_id)

    def get_minute(self, minute_id: str) -> dict[str, Any] | None:
        return self.minutes.get(minute_id)


def test_issue_stores_hash_and_builds_public_url():
    repo = _FakeInviteRepo()
    service = TmMeetingMinuteSignInviteService(
        repo, ttl_days=7, public_base_url="https://portal.delpi.local"
    )
    issued = service.issue(
        signer=repo.signers["s1"],
        minute=repo.minutes["m1"],
    )
    assert repo.invalidated == 1
    assert issued["raw_token"]
    assert hash_token(issued["raw_token"]) in repo.invites
    assert issued["sign_url"].startswith(
        "https://portal.delpi.local/p/transformometro/sign/"
    )


def test_resolve_happy_path():
    repo = _FakeInviteRepo()
    service = TmMeetingMinuteSignInviteService(repo, ttl_days=7)
    issued = service.issue(signer=repo.signers["s1"], minute=repo.minutes["m1"])
    resolved = service.resolve(issued["raw_token"])
    assert resolved["signer"]["id"] == "s1"
    assert resolved["minute"]["id"] == "m1"


def test_resolve_expired():
    repo = _FakeInviteRepo()
    service = TmMeetingMinuteSignInviteService(repo, ttl_days=7)
    issued = service.issue(signer=repo.signers["s1"], minute=repo.minutes["m1"])
    invite = repo.invites[hash_token(issued["raw_token"])]
    invite["expires_at"] = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValueError, match="expirou"):
        service.resolve(issued["raw_token"])


def test_resolve_consumed():
    repo = _FakeInviteRepo()
    service = TmMeetingMinuteSignInviteService(repo, ttl_days=7)
    issued = service.issue(signer=repo.signers["s1"], minute=repo.minutes["m1"])
    service.consume("inv-1")
    with pytest.raises(ValueError, match="utilizado"):
        service.resolve(issued["raw_token"])


def test_resolve_unknown_token():
    service = TmMeetingMinuteSignInviteService(_FakeInviteRepo(), ttl_days=7)
    with pytest.raises(LookupError):
        service.resolve("token-inexistente")
