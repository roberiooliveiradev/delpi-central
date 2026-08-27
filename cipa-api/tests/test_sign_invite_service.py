from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from cipa_app.application.services.cipa_meeting_minute_sign_invite_service import (
    CipaMeetingMinuteSignInviteService,
)
from cipa_app.application.services.token_service import hash_token


class _FakeInviteRepo:
    def __init__(self) -> None:
        self.invites: dict[str, dict[str, Any]] = {}
        self.invites_by_id: dict[str, dict[str, Any]] = {}
        self.signers: dict[str, dict[str, Any]] = {
            "s1": {
                "id": "s1",
                "status": "pending",
                "unit_code": "01",
                "display_name": "Ana",
                "user_id": "u1",
                "version_id": "v1",
            }
        }
        self.minutes: dict[str, dict[str, Any]] = {
            "m1": {
                "id": "m1",
                "unit_code": "01",
                "status": "awaiting_signatures",
                "deleted_at": None,
                "title": "Ata",
                "current_version_id": "v1",
            }
        }
        self.invalidated = 0

    def invalidate_open_invites(self, *, signer_id: str) -> int:
        self.invalidated += 1
        return 1

    def create_invite(self, **kwargs: Any) -> dict[str, Any]:
        row = {
            "id": f"inv-{len(self.invites_by_id) + 1}",
            "consumed_at": None,
            **kwargs,
        }
        self.invites[kwargs["token_hash"]] = row
        self.invites_by_id[row["id"]] = row
        return row

    def get_invite_by_token_hash(self, token_hash: str) -> dict[str, Any] | None:
        return self.invites.get(token_hash)

    def consume_invite(self, invite_id: str) -> dict[str, Any] | None:
        row = self.invites_by_id.get(invite_id)
        if not row:
            return None
        row["consumed_at"] = datetime.now(timezone.utc)
        return row

    def rebind_invite_signer(self, *, invite_id: str, signer_id: str) -> dict[str, Any] | None:
        row = self.invites_by_id.get(invite_id)
        if not row or row.get("consumed_at"):
            return None
        row["signer_id"] = signer_id
        return row

    def find_eligible_signer_match(
        self,
        *,
        minute_id: str,
        user_id: str | None,
    ) -> dict[str, Any] | None:
        minute = self.minutes.get(minute_id)
        if not minute:
            return None
        current = str(minute.get("current_version_id") or "")
        for signer in self.signers.values():
            if signer.get("status") not in {"pending", "viewed"}:
                continue
            if str(signer.get("version_id") or "") != current:
                continue
            if user_id and str(signer.get("user_id") or "") == user_id:
                return signer
        return None

    def get_signer(self, signer_id: str) -> dict[str, Any] | None:
        return self.signers.get(signer_id)

    def get_minute(self, minute_id: str) -> dict[str, Any] | None:
        return self.minutes.get(minute_id)


def test_issue_stores_hash_and_builds_public_url():
    repo = _FakeInviteRepo()
    service = CipaMeetingMinuteSignInviteService(
        repo, ttl_days=7, public_base_url="https://portal.delpi.local"
    )
    issued = service.issue(
        signer=repo.signers["s1"],
        minute=repo.minutes["m1"],
    )
    assert repo.invalidated == 1
    assert issued["raw_token"]
    assert hash_token(issued["raw_token"]) in repo.invites
    assert issued["sign_url"].startswith("https://portal.delpi.local/p/cipa/sign/")


def test_resolve_expired():
    repo = _FakeInviteRepo()
    service = CipaMeetingMinuteSignInviteService(repo, ttl_days=7)
    issued = service.issue(signer=repo.signers["s1"], minute=repo.minutes["m1"])
    invite = repo.invites[hash_token(issued["raw_token"])]
    invite["expires_at"] = datetime.now(timezone.utc) - timedelta(days=1)
    with pytest.raises(ValueError, match="expirou"):
        service.resolve(issued["raw_token"])
