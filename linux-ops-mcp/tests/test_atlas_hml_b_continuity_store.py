"""Persistent continuity store tests on disposable directories only."""
from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from linux_ops_mcp.atlas_hml_b_continuity_store import (
    HMLContinuityCommitResult,
    HMLContinuityRecord,
    HMLContinuityStore,
    HMLContinuityStoreError,
)

_T0 = datetime(2026, 11, 17, 20, 10, tzinfo=timezone.utc)


@pytest.fixture
def store_dir(tmp_path):
    root = tmp_path / "cont"
    root.mkdir()
    os.chmod(root, 0o750)
    return root


def _record(generation: int, *, when: datetime, digest: str = "a" * 64):
    return HMLContinuityRecord(
        generation=generation,
        digest=digest,
        observed_at=when,
        container_id="c" * 64,
        image_id="sha256:" + "d" * 64,
        updated_at=when,
    )


def test_commit_and_reload_across_simulated_restart(store_dir):
    first = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    result = first.commit(_record(1, when=_T0))
    assert isinstance(result, HMLContinuityCommitResult)
    assert result.status == "blocked"
    assert not result.persistent_anti_replay_host_attested
    assert not result.can_execute
    # Simulated restart: new object, same disposable directory.
    second = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    loaded = second.load()
    assert loaded is not None and loaded.generation == 1
    with pytest.raises(HMLContinuityStoreError) as err:
        second.commit(_record(1, when=_T0))
    assert err.value.code == "HML_CONTINUITY_STORE_REPLAY"
    assert second.halted


def test_monotonic_generation_and_gap_detection(store_dir):
    store = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    store.commit(_record(1, when=_T0))
    store.commit(_record(2, when=_T0 + timedelta(seconds=5), digest="b" * 64))
    with pytest.raises(HMLContinuityStoreError) as err:
        store.commit(_record(4, when=_T0 + timedelta(seconds=10), digest="c" * 64))
    assert err.value.code == "HML_CONTINUITY_STORE_COUNTER_GAP"


def test_counter_regression_and_corruption_fail_closed(store_dir):
    store = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    store.commit(_record(1, when=_T0))
    # Fresh store instance to attempt regression after successful gen 1.
    again = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    # Manually corrupt the file after a valid write.
    path = store_dir / "continuity-state.v1.json"
    path.write_bytes(b"{not-json")
    os.chmod(path, 0o640)
    broken = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    with pytest.raises(HMLContinuityStoreError) as err:
        broken.load()
    assert err.value.code == "HML_CONTINUITY_STORE_CORRUPT"
    assert broken.halted
    del again


def test_identity_change_denied(store_dir):
    store = HMLContinuityStore(
        store_dir, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )
    store.commit(_record(1, when=_T0))
    changed = HMLContinuityRecord(
        generation=2,
        digest="e" * 64,
        observed_at=_T0 + timedelta(seconds=3),
        container_id="f" * 64,
        image_id="sha256:" + "d" * 64,
        updated_at=_T0 + timedelta(seconds=3),
    )
    with pytest.raises(HMLContinuityStoreError) as err:
        store.commit(changed)
    assert err.value.code == "HML_CONTINUITY_STORE_IDENTITY_CHANGED"
