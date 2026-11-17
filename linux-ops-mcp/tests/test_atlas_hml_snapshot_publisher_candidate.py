"""Hermetic publisher and read-back tests: only pytest tmp_path receives writes.

The production directory /run/atlas-hml-readonly is not accessed, and no
Docker, systemd, network, service, privileged credentials or MCP execution
is created. The candidate remains fail-closed for PREPARE and ACT.
"""
from __future__ import annotations

import errno
import json
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp import atlas_hml_snapshot_publisher_candidate as candidate
from linux_ops_mcp import atlas_hml_snapshot_file_reader as reader
from linux_ops_mcp.deploy_host_source import RuntimeContainer


@pytest.fixture
def handoff(tmp_path):
    directory = tmp_path / "atlas-hml-fixture"
    directory.mkdir()
    os.chmod(directory, 0o750)
    now = datetime.now(timezone.utc)
    runtime = RuntimeContainer(
        container_id="a" * 64,
        image_id="sha256:" + "b" * 64,
        running=True, healthy=True,
    )
    raw = candidate.build_hml_snapshot_claim(runtime, observed_at=now)
    return directory, runtime, now, raw


def publish(handoff, *, raw=None, owner=None, gid=None, now=None):
    directory, _, observed_at, payload = handoff
    candidate._publish_in_review_directory(
        directory,
        raw=payload if raw is None else raw,
        owner_uid=os.getuid() if owner is None else owner,
        expected_gid=os.getgid() if gid is None else gid,
        now=observed_at if now is None else now,
    )


def read_back(handoff):
    directory, _, now, _ = handoff
    return reader._review_from_directory(
        directory,
        owner_uid=os.getuid(),
        expected_gid=os.getgid(),
        now=now,
    )


def assert_denied(code, func):
    with pytest.raises(candidate.HMLSnapshotPublishError) as exc:
        func()
    assert exc.value.code == code


def assert_clean_directory(handoff):
    directory = handoff[0]
    assert list(directory.glob(".atlas-hml-stage-*")) == []


def test_atomic_publication_roundtrips_through_existing_fd_reader(handoff):
    publish(handoff)
    result = read_back(handoff)
    assert result.status == "blocked"
    assert result.container_id == "a"*64
    assert result.image_id == "sha256:"+"b"*64
    assert result.environment == "hml"
    assert result.running and result.healthy
    assert not result.snapshot_origin_attested
    assert not result.docker_access_boundary_attested
    assert not result.prepare_eligible and not result.can_execute
    assert "ACT_DISABLED" in result.blocks
    file_path = handoff[0] / "inspect-snapshot.json"
    assert os.stat(file_path).st_mode & 0o777 == 0o640
    assert_clean_directory(handoff)


def test_second_generation_replaces_single_file_without_temp_leftovers(handoff):
    publish(handoff)
    directory, runtime, now, first = handoff
    old = (directory / "inspect-snapshot.json").read_bytes()
    updated = candidate.build_hml_snapshot_claim(
        replace(runtime, healthy=False), observed_at=now,
    )
    publish(handoff, raw=updated)
    new = (directory / "inspect-snapshot.json").read_bytes()
    assert old != new and old == first
    report = read_back(handoff)
    assert report.status == "blocked"
    assert not report.healthy
    assert "HML_CONTAINER_NOT_HEALTHY" in report.blocks
    assert not report.can_execute
    assert_clean_directory(handoff)


def test_only_fixed_hml_fields_are_serialized(handoff):
    _, _, _, raw = handoff
    data = json.loads(raw)
    assert set(data) == {
        "schema", "source", "environment", "compose_project", "service_id",
        "container_name", "container_id", "image_id", "running", "healthy",
        "observed_at",
    }
    assert "Env" not in data and "Mounts" not in data
    assert "token" not in raw.decode("ascii")
    assert len(raw) <= 2048


@pytest.mark.parametrize("changed", [
    {"container_id": "x"*64},
    {"image_id": "sha256:"+"B"*64},
    {"running": 1},
    {"healthy": "yes"},
])
def test_encoder_refuses_invalid_container_metadata(handoff, changed):
    _, runtime, now, _ = handoff
    with pytest.raises(candidate.HMLSnapshotPublishError, match="HML_SNAPSHOT_PRODUCER_INPUT_INVALID"):
        candidate.build_hml_snapshot_claim(replace(runtime, **changed), observed_at=now)


def test_encoder_rejects_naive_timestamp_and_non_runtime(handoff):
    _, runtime, now, _ = handoff
    with pytest.raises(candidate.HMLSnapshotPublishError, match="HML_SNAPSHOT_PRODUCER_INPUT_INVALID"):
        candidate.build_hml_snapshot_claim(runtime, observed_at=now.replace(tzinfo=None))
    with pytest.raises(candidate.HMLSnapshotPublishError, match="HML_SNAPSHOT_PRODUCER_INPUT_INVALID"):
        candidate.build_hml_snapshot_claim({"container_id": "a"*64}, observed_at=now)


def test_input_validation_runs_before_any_filesystem_write(handoff):
    directory, _, now, raw = handoff
    data = json.loads(raw)
    data["environment"] = "prod"
    before = list(directory.iterdir())
    assert_denied("HML_SNAPSHOT_TARGET_DENIED", lambda: publish(
        handoff, raw=json.dumps(data).encode(),
    ))
    assert list(directory.iterdir()) == before
    assert_clean_directory(handoff)


@pytest.mark.parametrize("mode", [0o700, 0o770, 0o751, 0o777])
def test_directory_mode_is_immutable_policy(handoff, mode):
    os.chmod(handoff[0], mode)
    assert_denied("HML_SNAPSHOT_DIRECTORY_UNSAFE", lambda: publish(handoff))
    assert_clean_directory(handoff)


def test_wrong_owner_or_group_never_creates_snapshot(handoff):
    assert_denied("HML_SNAPSHOT_DIRECTORY_UNSAFE", lambda: publish(
        handoff, owner=os.getuid()+1,
    ))
    assert_denied("HML_SNAPSHOT_DIRECTORY_UNSAFE", lambda: publish(
        handoff, gid=os.getgid()+1,
    ))
    assert_clean_directory(handoff)


def test_symlink_directory_is_denied_before_any_file_creation(handoff):
    directory, *_ = handoff
    other = directory.with_name("renamed")
    directory.rename(other)
    directory.symlink_to(other, target_is_directory=True)
    assert_denied("HML_SNAPSHOT_PUBLISH_UNAVAILABLE", lambda: publish(handoff))
    assert list(other.iterdir()) == []


@pytest.mark.parametrize("unsafe", ["symlink", "fifo", "hardlink", "mode"])
def test_unsafe_existing_destination_is_never_overwritten(handoff, unsafe):
    directory, _, _, _ = handoff
    file_path = directory / "inspect-snapshot.json"
    if unsafe == "symlink":
        outside = directory.with_name("outside-fixture")
        outside.write_bytes(b"original")
        file_path.symlink_to(outside)
    elif unsafe == "fifo":
        os.mkfifo(file_path, 0o640)
    else:
        file_path.write_bytes(b"original")
        if unsafe == "hardlink":
            os.link(file_path, directory / "also-linked")
        else:
            os.chmod(file_path, 0o666)

    assert_denied("HML_SNAPSHOT_DESTINATION_UNSAFE", lambda: publish(handoff))
    if unsafe == "symlink":
        assert outside.read_bytes() == b"original"
    elif unsafe != "fifo":
        assert file_path.read_bytes() == b"original"
    assert_clean_directory(handoff)


def test_atomic_replace_failure_preserves_last_valid_snapshot(handoff, monkeypatch):
    publish(handoff)
    old = (handoff[0] / "inspect-snapshot.json").read_bytes()
    def unavailable(*args, **kwargs):
        raise OSError(errno.EIO, "synthetic confidential replace path")
    monkeypatch.setattr(candidate.os, "replace", unavailable)
    assert_denied("HML_SNAPSHOT_PUBLISH_UNAVAILABLE", lambda: publish(handoff))
    assert (handoff[0] / "inspect-snapshot.json").read_bytes() == old
    assert_clean_directory(handoff)


def test_file_fsync_failure_preserves_old_snapshot_and_cleans_temp(handoff, monkeypatch):
    publish(handoff)
    old = (handoff[0] / "inspect-snapshot.json").read_bytes()
    def unavailable(_fd):
        raise OSError(errno.EIO, "private fake path")
    monkeypatch.setattr(candidate.os, "fsync", unavailable)
    assert_denied("HML_SNAPSHOT_PUBLISH_UNAVAILABLE", lambda: publish(handoff))
    assert (handoff[0] / "inspect-snapshot.json").read_bytes() == old
    assert_clean_directory(handoff)


def test_partial_write_does_not_publish_incomplete_snapshot(handoff, monkeypatch):
    publish(handoff)
    old = (handoff[0] / "inspect-snapshot.json").read_bytes()
    original = os.write
    def partial_then_fail(fd, data):
        if len(data) > 8:
            return original(fd, data[:8])
        return 0
    monkeypatch.setattr(candidate.os, "write", partial_then_fail)
    assert_denied("HML_SNAPSHOT_WRITE_FAILED", lambda: publish(handoff))
    assert (handoff[0] / "inspect-snapshot.json").read_bytes() == old
    assert_clean_directory(handoff)


def test_stage_path_replacement_cannot_be_committed(handoff, monkeypatch):
    publish(handoff)
    directory = handoff[0]
    old = (directory / "inspect-snapshot.json").read_bytes()
    original_fsync = os.fsync
    replaced = []
    def replace_stage_after_fsync(fd):
        original_fsync(fd)
        if not replaced:
            staged = list(directory.glob(".atlas-hml-stage-*"))
            assert len(staged) == 1
            stage = staged[0]
            detached = directory / "detached"
            stage.rename(detached)
            stage.write_bytes(b"attacker")
            os.chmod(stage, 0o640)
            replaced.append(True)
    monkeypatch.setattr(candidate.os, "fsync", replace_stage_after_fsync)
    assert_denied("HML_SNAPSHOT_STAGE_CHANGED", lambda: publish(handoff))
    assert (directory / "inspect-snapshot.json").read_bytes() == old
    assert_clean_directory(handoff)


def test_no_fchown_needed_when_fixture_matches_owner_group(handoff, monkeypatch):
    def forbidden(*args):
        raise AssertionError("must not change privileges in CI fixture")
    monkeypatch.setattr(candidate.os, "fchown", forbidden)
    publish(handoff)
    assert_clean_directory(handoff)


def test_stale_timestamp_claim_cannot_be_published(handoff):
    stale = handoff[2] - timedelta(minutes=2)
    updated = json.loads(handoff[3])
    updated["observed_at"] = stale.strftime("%Y-%m-%dT%H:%M:%SZ")
    assert_denied("HML_SNAPSHOT_EXPIRED_OR_FUTURE", lambda: publish(
        handoff, raw=json.dumps(updated).encode(),
    ))
    assert_clean_directory(handoff)


def test_candidate_has_no_production_entrypoint_or_mcp_interface():
    for name in (
        "main", "publish_fixed_snapshot", "start_producer", "serve",
        "create_mcp_server", "deploy", "get_docker_client",
    ):
        assert not hasattr(candidate, name)
