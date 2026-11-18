"""ATLAS B persisted-state adversarial cases, strictly temp directories.

Proves checks on open descriptors, ownership and inode identity, as well as
atomic read/commit under an advisory Linux directory lock. No real /run paths.
"""
from __future__ import annotations

import fcntl
import os
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp import atlas_hml_b_continuity_store as store_mod

T0 = datetime(2026, 11, 17, 22, 0, tzinfo=timezone.utc)


@pytest.fixture
def directory(tmp_path):
    root = tmp_path / "atlas-state"
    root.mkdir()
    os.chmod(root, 0o750)
    return root


def store(directory):
    return store_mod.HMLContinuityStore(
        directory, owner_uid=os.getuid(), expected_gid=os.getgid(),
    )


def record(n, when=None):
    when = T0 + timedelta(seconds=n)
    return store_mod.HMLContinuityRecord(
        generation=n, digest=(f"{n:064x}"),
        observed_at=when, container_id="a" * 64,
        image_id="sha256:" + "b" * 64, updated_at=when,
    )


def deny(code, f):
    with pytest.raises(store_mod.HMLContinuityStoreError) as error:
        f()
    assert error.value.code == code


def test_real_inode_checked_and_advisory_write_across_restart(directory):
    first = store(directory)
    assert first.load() is None
    first.commit(record(1))
    assert first.load() == record(1)
    second = store(directory)
    assert second.load() == record(1)
    second.commit(record(2))
    assert store(directory).load() == record(2)
    assert not second.halted


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo", "world", "directory"])
def test_dangerous_existing_continuity_state_is_refused(directory, kind):
    path = directory / store_mod._FILENAME
    obj = store(directory)
    obj.commit(record(1))
    if kind == "symlink":
        target = path.with_suffix(".old")
        path.rename(target)
        path.symlink_to(target)
    elif kind == "hardlink":
        os.link(path, path.with_suffix(".other"))
    elif kind == "fifo":
        path.unlink()
        os.mkfifo(path, 0o640)
    elif kind == "world":
        os.chmod(path, 0o644)
    elif kind == "directory":
        path.unlink()
        path.mkdir()
    deny("HML_CONTINUITY_STORE_FILE_UNSAFE", lambda: store(directory).load())


def test_directory_mode_or_owner_untrusted_denies_before_read(directory):
    state = store(directory)
    state.commit(record(1))
    os.chmod(directory, 0o755)
    deny("HML_CONTINUITY_STORE_DIR_UNSAFE", lambda: store(directory).load())


def test_state_disappearing_in_running_instance_latches(directory):
    instance = store(directory)
    instance.commit(record(1))
    (directory / store_mod._FILENAME).unlink()
    deny("HML_CONTINUITY_STORE_STATE_LOST", instance.load)
    deny("HML_CONTINUITY_STORE_STATE_LOST", lambda: instance.commit(record(2)))


def test_competing_process_directory_lock_fails_closed(directory):
    instance = store(directory)
    with os.fdopen(os.open(directory, os.O_RDONLY | os.O_DIRECTORY), "rb") as locked:
        fcntl.flock(locked.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        deny("HML_CONTINUITY_STORE_BUSY", lambda: instance.commit(record(1)))
    assert instance.halted
    assert not (directory / store_mod._FILENAME).exists()


def test_file_swap_after_descriptor_read_denied(directory, monkeypatch):
    store(directory).commit(record(1))
    old = store_mod.os.read
    path = directory / store_mod._FILENAME
    def swapping(fd, amount):
        result = old(fd, amount)
        # After bytes are read, a competing uncooperative actor swaps inode.
        temp = directory / "replacement"
        temp.write_bytes(result)
        os.chmod(temp, 0o640)
        os.replace(temp, path)
        return result
    monkeypatch.setattr(store_mod.os, "read", swapping)
    deny("HML_CONTINUITY_STORE_FILE_CHANGED", lambda: store(directory).load())


def test_acl_inspection_refusal_is_fail_closed(directory, monkeypatch):
    store(directory).commit(record(1))
    monkeypatch.setattr(store_mod, "has_no_extended_posix_acl",
                        lambda fd, *, directory: False)
    deny("HML_CONTINUITY_STORE_DIR_UNSAFE", lambda: store(directory).load())


def test_failed_directory_fsync_blocks_further_commits(directory, monkeypatch):
    current = store(directory)
    current.commit(record(1))
    original = store_mod.os.fsync
    def fail_directory(fd):
        if os.path.isdir(f"/proc/self/fd/{fd}"):
            raise OSError("synthetic fixture fsync failure")
        return original(fd)
    monkeypatch.setattr(store_mod.os, "fsync", fail_directory)
    deny("HML_CONTINUITY_STORE_WRITE_FAILED", lambda: current.commit(record(2)))
    assert current.halted
    deny("HML_CONTINUITY_STORE_WRITE_FAILED", lambda: current.commit(record(3)))


def test_stale_or_untrusted_candidate_rejected_before_write(directory):
    instance = store(directory)
    forged = store_mod.HMLContinuityRecord(
        generation=1, digest="x" * 64, observed_at=T0,
        container_id="a" * 64, image_id="sha256:" + "b" * 64,
        updated_at=T0,
    )
    deny("HML_CONTINUITY_STORE_INPUT_INVALID", lambda: instance.commit(forged))
    assert not (directory / store_mod._FILENAME).exists()


def test_unrecognized_bootstrap_state_remains_host_gate(directory):
    # A brand-new process cannot distinguish first boot from removed state.
    # This fixture documents the limitation rather than claiming protection.
    assert store(directory).load() is None
