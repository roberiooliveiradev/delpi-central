"""POSIX FD-to-continuity tests; temp files only, no host/Docker writes."""
from __future__ import annotations

import json
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp import atlas_hml_snapshot_file_reader as reader
from linux_ops_mcp.atlas_hml_b_snapshot_file_session import (
    HMLSnapshotFileSession, HMLSnapshotSessionError,
)

_BASE = {
    "schema": "atlas.hml.inspect.v1",
    "source": "root-one-shot-snapshot-claim-untrusted",
    "environment": "hml",
    "compose_project": "delpi-hml",
    "service_id": "public-hub",
    "container_name": "delpi-hml-public-hub",
    "container_id": "a" * 64, "image_id": "sha256:" + "b" * 64,
    "running": True, "healthy": True,
}


@pytest.fixture
def store(tmp_path):
    now = datetime.now(timezone.utc).replace(microsecond=0)
    root = tmp_path / "hml-disposable"
    root.mkdir()
    os.chmod(root, 0o750)
    path = root / "inspect-snapshot.json"
    _replace(path, now)
    return root, path, now


def _bytes(observed_at, **changes):
    return json.dumps({
        **_BASE,
        "observed_at": observed_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        **changes,
    }, separators=(",", ":"), sort_keys=True).encode("ascii")


def _replace(path, observed_at, **changes):
    staged = path.with_name(".staged-fixture")
    staged.write_bytes(_bytes(observed_at, **changes))
    os.chmod(staged, 0o640)
    os.replace(staged, path)


def _record(store, *, now=None):
    root, _, instant = store
    return reader._read_record_from_directory(
        root,
        owner_uid=os.getuid(), expected_gid=os.getgid(),
        now=instant if now is None else now,
    )


def _deny(session, code, record, now, count):
    with pytest.raises(HMLSnapshotSessionError) as error:
        session.observe(record, now=now, monotonic_ns=count)
    assert error.value.code == code
    assert session.halted


def test_fd_checked_read_and_same_inode_repeated_get_allowed(store):
    session = HMLSnapshotFileSession()
    a = _record(store)
    assert a.raw and a.inode > 0
    assert a.diagnostic.status == "blocked"
    first = session.observe(a, now=store[2], monotonic_ns=100)
    second = session.observe(_record(store, now=store[2] + timedelta(seconds=2)),
                             now=store[2] + timedelta(seconds=2), monotonic_ns=110)
    for result in (first, second):
        assert result.status == "blocked" and result.fixture_continuity_ok
        assert not result.producer_authenticated
        assert not result.replay_protection_persistent
        assert not result.host_attested
        assert not result.can_execute and not result.prepare_eligible
        assert "ACT_DISABLED" in result.blocks
    assert not session.halted


def test_atomic_replacement_with_new_timestamp_is_allowed_but_never_authorized(store):
    session = HMLSnapshotFileSession()
    session.observe(_record(store), now=store[2], monotonic_ns=100)
    next_time = store[2] + timedelta(seconds=10)
    _replace(store[1], next_time)
    second = _record(store, now=next_time)
    outcome = session.observe(second, now=next_time, monotonic_ns=200)
    assert outcome.fixture_continuity_ok and not outcome.can_execute


def test_republished_same_generation_is_replay(store):
    session = HMLSnapshotFileSession()
    session.observe(_record(store), now=store[2], monotonic_ns=100)
    _replace(store[1], store[2])
    newer = _record(store, now=store[2] + timedelta(seconds=1))
    _deny(session, "HML_SESSION_REPLAY_OR_REGRESSION",
          newer, store[2] + timedelta(seconds=1), 110)


def test_inplace_mutation_is_denied(store):
    session = HMLSnapshotFileSession()
    session.observe(_record(store), now=store[2], monotonic_ns=100)
    store[1].write_bytes(_bytes(store[2], healthy=False))
    os.chmod(store[1], 0o640)
    modified = _record(store, now=store[2] + timedelta(seconds=2))
    _deny(session, "HML_SESSION_INPLACE_MUTATION", modified,
          store[2] + timedelta(seconds=2), 110)


@pytest.mark.parametrize("attribute,value", [
    ("image_id", "sha256:" + "c" * 64),
    ("container_id", "d" * 64),
])
def test_unreviewed_replacements_of_target_identity_are_denied(store, attribute, value):
    session = HMLSnapshotFileSession()
    session.observe(_record(store), now=store[2], monotonic_ns=100)
    fresh = store[2] + timedelta(seconds=10)
    _replace(store[1], fresh, **{attribute: value})
    _deny(session, "HML_SESSION_UNREVIEWED_IDENTITY_CHANGE",
          _record(store, now=fresh), fresh, 200)


def test_out_of_order_clock_and_monotonic_read_fail_stop(store):
    session = HMLSnapshotFileSession()
    old = _record(store)
    session.observe(old, now=store[2], monotonic_ns=100)
    _deny(session, "HML_SESSION_MONOTONIC_REGRESSION", old,
          store[2] + timedelta(seconds=1), 100)
    # The fault cannot be reset by a later good snapshot or timestamp.
    _deny(session, "HML_SESSION_MONOTONIC_REGRESSION", old,
          store[2] + timedelta(seconds=2), 200)


def test_operator_failure_and_shutdown_are_latched_no_auto_rollback(store):
    for code in ("HML_SESSION_PRODUCER_FAILED", "HML_SESSION_PUBLISH_FAILED",
                 "HML_SESSION_SNAPSHOT_UNAVAILABLE", "HML_SESSION_PROCESS_UNSAFE",
                 "HML_SESSION_SHUTDOWN_REQUESTED"):
        session = HMLSnapshotFileSession()
        session.observe(_record(store), now=store[2], monotonic_ns=100)
        with pytest.raises(HMLSnapshotSessionError) as error:
            session.mark_failure(code)
        assert error.value.code == code
        _deny(session, code, _record(store), store[2], 200)


def test_inconsistent_fixture_metadata_and_expired_bytes_denied(store):
    session = HMLSnapshotFileSession()
    record = _record(store)
    forged = replace(record, diagnostic=replace(record.diagnostic, can_execute=True))
    _deny(session, "HML_SESSION_RECORD_INCONSISTENT", forged, store[2], 100)

    session = HMLSnapshotFileSession()
    # Even if a record was fresh when opened, time can elapse before consume.
    _deny(session, "HML_SESSION_SNAPSHOT_UNAVAILABLE", record,
          store[2] + timedelta(seconds=90), 100)


def test_reader_refuses_untrusted_symlink_before_session(store):
    path = store[1]
    moved = path.with_suffix(".bak")
    path.rename(moved)
    path.symlink_to(moved)
    with pytest.raises(reader.HMLSnapshotFileError):
        _record(store)


def test_invalid_fault_code_latches_not_starting_host_cleanup(store):
    session = HMLSnapshotFileSession()
    with pytest.raises(HMLSnapshotSessionError) as error:
        session.mark_failure("docker restart")
    assert error.value.code == "HML_SESSION_FAULT_INVALID"
    assert session.halted
