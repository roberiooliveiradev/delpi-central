"""Offline P2.2c: all journal decisions require a future DB lock/UNIQUE."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.deploy_journal_policy import PrepareRecord, decide_prepare_insert

NOW = datetime(2026, 11, 15, 15, 0, tzinfo=timezone.utc)


def candidate(**changes):
    record = PrepareRecord(
        request_id="01234567-89ab-4def-8abc-0123456789ab",
        requester_subject="11111111-2222-4333-8444-555555555555",
        environment="hml", service_id="it-portal-api",
        target_sha="a" * 40, base_sha="b" * 40, proposal_hash="c" * 64,
        created_at=NOW, expires_at=NOW + timedelta(minutes=10),
    )
    return replace(record, **changes)


def decide(row=None, **changes):
    return decide_prepare_insert(candidate=candidate(**changes), existing=row, now=NOW)


def test_new_candidate_is_not_approval_and_replay_does_not_write():
    record = candidate()
    assert decide().state == "create_candidate"
    assert decide(row=record).state == "replay_pending"
    assert record.status == "pending_approval"


def test_modified_payload_with_same_idempotency_key_conflicts():
    row = candidate()
    assert decide(row=row, target_sha="d" * 40).reason == "IDEMPOTENCY_PAYLOAD_MISMATCH"
    assert decide(row=row, proposal_hash="e" * 64).state == "conflict"


def test_different_actor_or_request_cannot_reuse_row():
    assert decide(row=candidate(requester_subject="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")).reason == "JOURNAL_IDENTITY_MISMATCH"
    assert decide(row=candidate(request_id="aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee")).reason == "JOURNAL_IDENTITY_MISMATCH"


@pytest.mark.parametrize("changes", [
    {"request_id": "x"}, {"requester_subject": "user-001"},
    {"environment": "dev"}, {"service_id": "../../it-portal-api"},
    {"target_sha": "latest"}, {"base_sha": "b" * 39},
    {"proposal_hash": "c" * 63}, {"status": "approved"},
    {"target_sha": "b" * 40}, {"created_at": NOW.replace(tzinfo=None)},
    {"expires_at": NOW + timedelta(minutes=11)},
    {"expires_at": NOW - timedelta(seconds=1)},
    {"created_at": NOW + timedelta(seconds=6)},
])
def test_invalid_candidate_blocks(changes):
    assert decide(**changes).state == "blocked"


def test_invalid_now_and_journal_row_block():
    assert decide_prepare_insert(candidate=candidate(), existing=None, now=NOW.replace(tzinfo=None)).state == "blocked"
    assert decide_prepare_insert(candidate=candidate(), existing={"trusted": True}, now=NOW).state == "blocked"
