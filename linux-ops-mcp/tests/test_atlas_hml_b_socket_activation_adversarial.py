"""Dedicated LISTEN_* denial matrix for Linux presenter candidate.

Pure environment fixtures. No socket creation, systemd activation, Docker or
host mutation. A clean parse is only an input consistency check, not SEC-03.
"""
from __future__ import annotations

import pytest

from linux_ops_mcp import atlas_hml_b_presenter_process_guard as guard


@pytest.fixture
def fake_systemd(monkeypatch):
    monkeypatch.setattr(guard.os, "getpid", lambda: 31415)
    monkeypatch.setattr(guard.os, "environ", {})
    return guard.os.environ


@pytest.mark.parametrize("key,value", [
    ("LISTEN_PID", "31415"),
    ("LISTEN_FDS", "1"),
    ("LISTEN_FDNAMES", "inspect"),
])
def test_partial_activation_tuple_is_denied(fake_systemd, key, value):
    fake_systemd[key] = value
    assert not guard._socket_activation_consistent(3)


def test_no_activation_vars_is_allowed_for_disposable_fixture_only(fake_systemd):
    assert guard._socket_activation_consistent(8)


def test_exact_one_listener_is_consistent_but_not_host_attestation(fake_systemd):
    fake_systemd.update({
        "LISTEN_PID": "31415",
        "LISTEN_FDS": "1",
        "LISTEN_FDNAMES": "inspect",
    })
    assert guard._socket_activation_consistent(3)
    assert not guard._socket_activation_consistent(4)


@pytest.mark.parametrize("key,value", [
    ("LISTEN_PID", "31416"),
    ("LISTEN_PID", "031415"),
    ("LISTEN_PID", "31415 "),
    ("LISTEN_PID", "abc"),
    ("LISTEN_PID", "-1"),
    ("LISTEN_FDS", "0"),
    ("LISTEN_FDS", "2"),
    ("LISTEN_FDS", "01"),
    ("LISTEN_FDS", "1\n"),
    ("LISTEN_FDNAMES", ""),
    ("LISTEN_FDNAMES", "a:b"),
    ("LISTEN_FDNAMES", "../docker.sock"),
    ("LISTEN_FDNAMES", "inspect\n"),
    ("LISTEN_FDNAMES", "Inspect"),
    ("LISTEN_FDNAMES", "a" * 33),
    ("LISTEN_FDNAMES", "docker socket"),
])
def test_wrong_activation_value_is_rejected(fake_systemd, key, value):
    fake_systemd.update({
        "LISTEN_PID": "31415",
        "LISTEN_FDS": "1",
        "LISTEN_FDNAMES": "inspect",
    })
    fake_systemd[key] = value
    assert not guard._socket_activation_consistent(3)


@pytest.mark.parametrize("key", [
    "LISTEN_FDS_EXTRA", "LISTEN_PID_OVERRIDE", "LISTEN_FDNAMES_ALT",
    "LISTEN_DOCKER_SOCKET", "LISTEN_MY_SOCKET",
])
def test_unexpected_activation_variable_denied(fake_systemd, key):
    fake_systemd.update({
        "LISTEN_PID": "31415",
        "LISTEN_FDS": "1",
        "LISTEN_FDNAMES": "inspect",
        key: "1",
    })
    assert not guard._socket_activation_consistent(3)


def test_unexpected_only_activation_variable_denied(fake_systemd):
    fake_systemd["LISTEN_DOCKER_SOCKET"] = "/run/docker.sock"
    assert not guard._socket_activation_consistent(3)


def test_listen_value_never_appears_in_error_or_attestation(fake_systemd):
    fake_systemd.update({
        "LISTEN_PID": "31415",
        "LISTEN_FDS": "1",
        "LISTEN_FDNAMES": "inspect:secret",
    })
    assert not guard._socket_activation_consistent(3)
    report = guard.PresenterProcessReview()
    assert report.status == "blocked"
    assert not report.can_execute and not report.prepare_eligible
    assert "secret" not in repr(report)
