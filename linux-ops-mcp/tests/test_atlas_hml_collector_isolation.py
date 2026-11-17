"""Read-only collector process isolation review: negative cases and safe CLI.

All filesystem fixtures live under pytest tmp_path. Never opens a Docker
socket, runs Docker/systemd, reads real host secrets, changes privileges or
enables PREPARE/ACT.
"""
from __future__ import annotations

import json
import os
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

from linux_ops_mcp import atlas_hml_collector_isolation as review

SAFE = review.CollectorPostureFacts(
    named_account_matches_process=True,
    nologin_shell=True,
    primary_group_exclusive=True,
    privileged_groups_absent=True,
    checkout_write_denied=True,
    raw_socket_write_denied=True,
    capabilities_zero=True,
    permitted_capabilities_zero=True,
    ambient_capabilities_zero=True,
    no_new_privileges=True,
    seccomp_filter=True,
    alternate_docker_env_unset=True,
)


def test_even_every_observed_dac_and_proc_check_passes_never_grants_authority():
    outcome = review.review_facts(SAFE)
    assert outcome.status == "blocked"
    assert outcome.environment == "hml" and outcome.service_id == "public-hub"
    assert not outcome.prepare_eligible and not outcome.can_execute
    assert not outcome.host_identity_attested
    assert not outcome.upstream_process_attested
    assert not outcome.proxy_policy_independently_attested
    assert not outcome.checkout_integrity_attested
    assert not outcome.challenge_consumed
    assert "PREPARE_DISABLED" in outcome.blocks
    assert "ACT_DISABLED" in outcome.blocks
    assert "RAW_DOCKER_ENDPOINTS_NOT_EXHAUSTIVELY_ATTESTED" in outcome.blocks
    assert "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED" in outcome.blocks
    assert not any(block.startswith("/") for block in outcome.blocks)


@pytest.mark.parametrize("field,code", review._CHECKS)
@pytest.mark.parametrize("value", [False, None])
def test_failing_or_unknown_observation_is_finite_and_blocked(field, code, value):
    outcome = review.review_facts(replace(SAFE, **{field: value}))
    assert code in outcome.blocks
    assert outcome.prepare_eligible is False and outcome.can_execute is False


@pytest.mark.parametrize("field", [name for name, _ in review._CHECKS])
@pytest.mark.parametrize("bad", [1, "true", [], {"authorized": True}])
def test_non_boolean_claims_are_rejected_and_cannot_promote_auth(field, bad):
    with pytest.raises(review.CollectorReviewError, match="ATLAS_COLLECTOR_FACTS_INVALID"):
        review.review_facts(replace(SAFE, **{field: bad}))


def test_non_dataclass_observation_is_rejected():
    with pytest.raises(review.CollectorReviewError, match="ATLAS_COLLECTOR_FACTS_INVALID"):
        review.review_facts(asdict(SAFE))


def test_proc_status_parses_only_security_flags_from_bounded_input(tmp_path):
    path = tmp_path / "proc-fixture"
    path.write_text(
        "Name:\tfixture\n"
        "CapEff:\t0000000000000000\n"
        "CapPrm:\t0000000000000000\n"
        "CapAmb:\t0000000000000000\n"
        "NoNewPrivs:\t1\n"
        "Seccomp:\t2\n",
        encoding="ascii",
    )
    assert review._proc_flags(path) == (True, True, True, True, True)
    path.write_text(
        "CapEff:\t0000000000000001\n"
        "CapPrm:\t0000000000000001\n"
        "CapAmb:\t0000000000000001\n"
        "NoNewPrivs:\t0\n"
        "Seccomp:\t0\n", encoding="ascii",
    )
    assert review._proc_flags(path) == (False, False, False, False, False)
    path.write_text("CapEff:bad-hex\n", encoding="ascii")
    assert review._proc_flags(path) == (None, None, None, None, None)
    path.write_bytes(b"X" * 8193)
    assert review._proc_flags(path) == (None, None, None, None, None)


def test_raw_docker_dac_observation_does_not_connect(tmp_path, monkeypatch):
    raw = tmp_path / "fake-docker.sock"
    monkeypatch.setattr(review, "_RAW_DOCKER_SOCKETS", (raw,))
    assert review._raw_socket_denied() is True  # path absent
    raw.touch()
    monkeypatch.setattr(review.os, "access", lambda path, mode, effective_ids=False: False)
    assert review._raw_socket_denied() is True
    monkeypatch.setattr(review.os, "access", lambda path, mode, effective_ids=False: True)
    assert review._raw_socket_denied() is False


def test_missing_checkout_never_claims_write_is_denied(tmp_path):
    missing = tmp_path / "not-present"
    assert review._writable(missing) is None


def test_writable_metadata_failure_stays_unknown(tmp_path, monkeypatch):
    present = tmp_path / "observed"
    present.touch()
    def unavailable(*args, **kwargs):
        raise PermissionError("synthetic-private-host-metadata")
    monkeypatch.setattr(review.os, "access", unavailable)
    assert review._writable(present) is None


def test_account_and_kernel_flags_are_observed_without_exposing_identity(
    monkeypatch,
):
    acct = SimpleNamespace(pw_uid=995, pw_gid=985, pw_shell="/usr/sbin/nologin")
    grp_obj = SimpleNamespace(gr_gid=985, gr_name="atlas-hml")
    monkeypatch.setattr(review.pwd, "getpwnam", lambda name: acct)
    monkeypatch.setattr(review.grp, "getgrnam", lambda name: grp_obj)
    monkeypatch.setattr(review.grp, "getgrgid", lambda gid: grp_obj)
    monkeypatch.setattr(review.os, "getuid", lambda: 995)
    monkeypatch.setattr(review.os, "geteuid", lambda: 995)
    monkeypatch.setattr(review.os, "getgid", lambda: 985)
    monkeypatch.setattr(review.os, "getegid", lambda: 985)
    monkeypatch.setattr(review.os, "getgroups", lambda: [985])
    monkeypatch.setattr(
        review, "_proc_flags", lambda: (True, True, True, True, True),
    )
    monkeypatch.setattr(review, "_writable", lambda path: False)
    monkeypatch.setattr(review, "_raw_socket_denied", lambda: True)
    for key in review._ALTERNATE_ENV:
        monkeypatch.delenv(key, raising=False)
    observed = review.observe_current_process()
    assert observed == SAFE
    assert "995" not in str(observed)
    assert "985" not in str(observed)
    monkeypatch.setenv("DOCKER_HOST", "tcp://example.invalid:2375")
    assert review.observe_current_process().alternate_docker_env_unset is False


def test_privileged_supplementary_group_is_detected(monkeypatch):
    acct = SimpleNamespace(pw_uid=995, pw_gid=985, pw_shell="/usr/sbin/nologin")
    monkeypatch.setattr(review.pwd, "getpwnam", lambda _: acct)
    monkeypatch.setattr(
        review.grp, "getgrnam",
        lambda _: SimpleNamespace(gr_gid=985, gr_name="atlas-hml"),
    )
    monkeypatch.setattr(
        review.grp, "getgrgid",
        lambda gid: SimpleNamespace(gr_name="docker" if gid == 999 else "atlas-hml"),
    )
    monkeypatch.setattr(review.os, "getuid", lambda: 995)
    monkeypatch.setattr(review.os, "geteuid", lambda: 995)
    monkeypatch.setattr(review.os, "getgid", lambda: 985)
    monkeypatch.setattr(review.os, "getegid", lambda: 985)
    monkeypatch.setattr(review.os, "getgroups", lambda: [985, 999])
    monkeypatch.setattr(review, "_proc_flags", lambda: (None,) * 5)
    monkeypatch.setattr(review, "_writable", lambda path: None)
    monkeypatch.setattr(review, "_raw_socket_denied", lambda: None)
    facts = review.observe_current_process()
    assert facts.privileged_groups_absent is False
    assert "COLLECTOR_PRIVILEGED_GROUP_PRESENT_OR_UNKNOWN" in review.review_facts(facts).blocks


def test_manual_cli_returns_only_sanitized_denial(monkeypatch, capsys):
    monkeypatch.setattr(review, "observe_current_process", lambda: SAFE)
    assert review.main() == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "blocked"
    assert not payload["prepare_eligible"] and not payload["can_execute"]
    assert payload["checks"]["raw_socket_write_denied"] is True
    assert "PREPARE_DISABLED" in payload["blocks"]


def test_unexpected_os_error_is_sanitized(monkeypatch, capsys):
    def leak():
        raise RuntimeError("SYNTHETIC_SUPER_SECRET_DO_NOT_PRINT")
    monkeypatch.setattr(review, "observe_current_process", leak)
    assert review.main() == 2
    output = capsys.readouterr().out
    assert "SYNTHETIC_SUPER_SECRET" not in output
    assert json.loads(output) == {
        "status": "blocked", "code": "ATLAS_COLLECTOR_REVIEW_UNAVAILABLE",
        "prepare_eligible": False, "can_execute": False,
    }


def test_module_has_no_service_or_mcp_entrypoint():
    assert not hasattr(review, "serve")
    assert not hasattr(review, "deploy")
    assert not hasattr(review, "create_mcp_server")
    text = Path(review.__file__).read_text(encoding="utf-8")
    for forbidden in ("subprocess.", "docker.sock).connect(", "os.chmod(", "os.chown("):
        assert forbidden not in text
