"""Source-only guard tests. Kernel-alike data is synthetic, never host proof."""
from __future__ import annotations

import os
import socket
from dataclasses import replace

import pytest

from linux_ops_mcp import atlas_hml_b_presenter_process_guard as guard


@pytest.fixture
def prebound(tmp_path, monkeypatch):
    path = tmp_path / "review.sock"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind(str(path))
        listener.listen(1)
        values = {
            "uids": (1001,) * 4, "gids": (1002,) * 4,
            "groups": (), "caps": (0, 0, 0, 0, 0),
            "nnp": 1, "seccomp": 2,
        }
        monkeypatch.setattr(guard, "_read_status", lambda: values)
        monkeypatch.setattr(guard, "_fd_set", lambda: ((listener.fileno(), True),))
        monkeypatch.setattr(guard.os, "getresuid", lambda: (1001,) * 3)
        monkeypatch.setattr(guard.os, "getresgid", lambda: (1002,) * 3)
        monkeypatch.setattr(guard.os, "getgroups", lambda: [])
        monkeypatch.setattr(guard.os, "environ", {})
        yield listener, path, values


def check(prebound):
    listener, path, _ = prebound
    return guard._review_prebound_process_fixture(
        listener, expected_uid=1001, expected_gid=1002,
        expected_path=path,
    )


def test_positive_fixture_still_never_attests_host(prebound):
    report = check(prebound)
    assert report.status == "blocked"
    assert report.identity_fd_preflight_passed
    assert report.sandbox_basics_observed
    assert not report.host_isolation_attested
    assert not report.docker_isolation_attested
    assert not report.producer_privilege_attested
    assert not report.operational_authorization_granted
    assert not report.can_execute and not report.prepare_eligible
    assert "PREPARE_DISABLED" in report.blocks and "ACT_DISABLED" in report.blocks


@pytest.mark.parametrize("change,expected", [
    ({"uids": (0, 1001, 1001, 1001)}, "HML_PRESENTER_IDENTITY_DENIED"),
    ({"gids": (1002, 1002, 0, 1002)}, "HML_PRESENTER_IDENTITY_DENIED"),
    ({"groups": (999,)}, "HML_PRESENTER_IDENTITY_DENIED"),
    ({"caps": (0, 0, 1, 0, 0)}, "HML_PRESENTER_CAPABILITIES_DENIED"),
    ({"caps": (0, 0, 0, 1, 0)}, "HML_PRESENTER_SANDBOX_NOT_CONFIRMED"),
    ({"nnp": 0}, "HML_PRESENTER_SANDBOX_NOT_CONFIRMED"),
    ({"seccomp": 0}, "HML_PRESENTER_SANDBOX_NOT_CONFIRMED"),
])
def test_denied_privilege_or_sandbox_drift(prebound, change, expected):
    prebound[2].update(change)
    result = check(prebound)
    assert expected in result.blocks
    assert result.status == "blocked" and not result.can_execute
    if "SANDBOX" in expected:
        assert not result.sandbox_basics_observed


def test_docker_fd_and_unknown_regular_fd_denied(prebound, monkeypatch):
    listener, _, _ = prebound
    for fd in (((listener.fileno(), True), (29, True)),
               ((listener.fileno(), True), (30, False))):
        monkeypatch.setattr(guard, "_fd_set", lambda fd=fd: fd)
        result = check(prebound)
        assert not result.identity_fd_preflight_passed
        assert "HML_PRESENTER_FD_BOUNDARY_DENIED" in result.blocks


def test_env_transport_alias_and_injection_denied(prebound, monkeypatch):
    for env in ({"DOCKER_HOST": "tcp://some-host"},
                {"DOCKER_CUSTOM_ENDPOINT": "unix:///tmp/alias.sock"},
                {"LD_PRELOAD": "unsafe.so"}, {"SSH_AUTH_SOCK": "/tmp/ssh.sock"}):
        monkeypatch.setattr(guard.os, "environ", env)
        result = check(prebound)
        assert not result.identity_fd_preflight_passed
        assert "HML_PRESENTER_ENVIRONMENT_DENIED" in result.blocks


def test_path_or_socket_mismatch_denied(prebound):
    listener, path, _ = prebound
    report = guard._review_prebound_process_fixture(
        listener, expected_uid=1001, expected_gid=1002,
        expected_path=path.with_name("other.sock"),
    )
    assert "HML_PRESENTER_FD_BOUNDARY_DENIED" in report.blocks


def test_bad_input_and_unverifiable_proc_fail_closed(prebound, monkeypatch):
    listener, path, _ = prebound
    with pytest.raises(guard.HMLPresenterBoundaryError) as exc:
        guard._review_prebound_process_fixture(
            listener, expected_uid=0, expected_gid=1002, expected_path=path,
        )
    assert exc.value.code == "HML_PRESENTER_POLICY_INVALID"
    monkeypatch.setattr(
        guard, "_read_status", lambda: (_ for _ in ()).throw(
            guard.HMLPresenterBoundaryError("HML_PRESENTER_PROC_UNVERIFIABLE")
        ),
    )
    with pytest.raises(guard.HMLPresenterBoundaryError) as exc:
        check(prebound)
    assert exc.value.code == "HML_PRESENTER_PROC_UNVERIFIABLE"


def test_no_entrypoint_or_privilege_mutation():
    for name in ("main", "run", "start", "install", "serve", "deploy"):
        assert not hasattr(guard, name)
