"""Pure replay/failure tests for an untrusted in-memory HML snapshot ledger."""
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_snapshot_continuity import (
    HMLSnapshotContinuityError, review_snapshot_continuity,
)

NOW = datetime(2026, 11, 17, 15, 0, tzinfo=timezone.utc)
BASE = {
    "schema": "atlas.hml.inspect.v1",
    "source": "root-one-shot-snapshot-claim-untrusted",
    "environment": "hml",
    "compose_project": "delpi-hml", "service_id": "public-hub",
    "container_name": "delpi-hml-public-hub",
    "container_id": "a" * 64, "image_id": "sha256:" + "b" * 64,
    "running": True, "healthy": True,
}


def claim(moment=NOW, **changes):
    return json.dumps({
        **BASE, "observed_at": moment.isoformat().replace("+00:00", "Z"),
        **changes,
    }, sort_keys=True).encode()


def rejected(code, run):
    with pytest.raises(HMLSnapshotContinuityError) as exc:
        run()
    assert exc.value.code == code


def test_initial_and_next_generation_remain_blocked():
    a = review_snapshot_continuity(claim(), now=NOW)
    b = review_snapshot_continuity(
        claim(NOW + timedelta(seconds=10)),
        now=NOW + timedelta(seconds=10), previous=a.next_state,
    )
    assert a.status == b.status == "blocked"
    assert not b.can_execute and not b.prepare_eligible
    assert not b.origin_attested and not b.replay_attested
    assert b.next_state.observed_at > a.next_state.observed_at


def test_replay_conflict_and_clock_regression_are_denied():
    old = review_snapshot_continuity(claim(), now=NOW).next_state
    rejected("HML_CONTINUITY_REPLAY", lambda: review_snapshot_continuity(
        claim(), now=NOW, previous=old,
    ))
    rejected("HML_CONTINUITY_GENERATION_CONFLICT", lambda: review_snapshot_continuity(
        claim(healthy=False), now=NOW, previous=old,
    ))
    rejected("HML_CONTINUITY_TIME_REGRESSION", lambda: review_snapshot_continuity(
        claim(NOW - timedelta(seconds=1)), now=NOW, previous=old,
    ))


def test_image_and_container_changes_need_external_generation_authority():
    old = review_snapshot_continuity(claim(), now=NOW).next_state
    later = NOW + timedelta(seconds=10)
    for change in ({"image_id": "sha256:" + "c" * 64},
                   {"container_id": "d" * 64}):
        rejected("HML_CONTINUITY_IDENTITY_CHANGED", lambda: review_snapshot_continuity(
            claim(later, **change), now=later, previous=old,
        ))


def test_stale_future_prod_and_malformed_are_denied():
    for data, instant in (
        (claim(NOW - timedelta(seconds=61)), NOW),
        (claim(NOW + timedelta(seconds=6)), NOW),
        (claim(environment="prod"), NOW),
        (b"secret:bad", NOW),
    ):
        with pytest.raises(HMLSnapshotContinuityError):
            review_snapshot_continuity(data, now=instant)


def test_forged_state_is_denied():
    old = review_snapshot_continuity(claim(), now=NOW).next_state
    rejected("HML_CONTINUITY_STATE_UNTRUSTED", lambda: review_snapshot_continuity(
        claim(NOW + timedelta(seconds=1)),
        now=NOW + timedelta(seconds=1), previous=replace(old, digest="broken"),
    ))


def test_failure_does_not_mutate_previous_state():
    old = review_snapshot_continuity(claim(), now=NOW).next_state
    rejected("HML_CONTINUITY_REPLAY", lambda: review_snapshot_continuity(
        claim(), now=NOW, previous=old,
    ))
    assert old.observed_at == NOW
