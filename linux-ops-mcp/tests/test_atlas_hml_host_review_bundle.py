"""Offline and disposable tests for the HML read-only review dossier.

Never calls Docker, starts a listener, modifies a real user/host, runs Git,
or emits authority for PREPARE/ACT.
"""
from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import datetime, timezone

import pytest

from linux_ops_mcp import atlas_hml_host_review_bundle as dossier
from linux_ops_mcp.atlas_hml_collector_isolation import CollectorPostureFacts
from linux_ops_mcp.atlas_hml_git_head_peek import UntrustedGitHead
from linux_ops_mcp.atlas_hml_uds_policy import HMLUDSPolicyError

NOW = datetime(2026, 11, 17, 14, 0, tzinfo=timezone.utc)
SAFE = CollectorPostureFacts(**{
    name: True for name in CollectorPostureFacts.__dataclass_fields__
})
META = UntrustedGitHead(branch="main", head_sha="a"*40)


def assert_blocked(bundle):
    assert bundle.status == "blocked"
    assert bundle.environment == "hml"
    assert bundle.service_id == "public-hub"
    assert bundle.observed_at == "2026-11-17T14:00:00+00:00"
    assert not bundle.host_identity_attested
    assert not bundle.collector_transport_attested
    assert not bundle.proxy_policy_independently_attested
    assert not bundle.checkout_integrity_attested
    assert not bundle.challenge_consumed
    assert not bundle.prepare_eligible
    assert not bundle.can_execute
    assert "PREPARE_DISABLED" in bundle.blocks
    assert "ACT_DISABLED" in bundle.blocks
    assert "INDEPENDENT_SECURITY_REVIEW_REQUIRED" in bundle.blocks


def test_all_technical_flags_true_still_only_metadata():
    bundle = dossier.assemble_bundle(
        facts=SAFE, git=META, proxy_state="metadata_only_untrusted", now=NOW,
    )
    assert_blocked(bundle)
    assert bundle.git_branch == "main"
    assert bundle.git_head_metadata_only_untrusted == "a"*40
    assert bundle.git_clean_status_observed is False
    assert bundle.proxy_socket_metadata == "metadata_only_untrusted"
    assert "HML_GIT_STATUS_NOT_CHECKED" in bundle.blocks
    assert "GIT_FILESYSTEM_SNAPSHOT_NOT_ATOMIC" in bundle.blocks
    assert "HML_PROXY_POLICY_NOT_INDEPENDENTLY_ATTESTED" in bundle.blocks


@pytest.mark.parametrize("field", dossier._UNSAFE_TO_READ)
def test_unsafe_collector_never_exposes_git_or_socket_metadata(field):
    unsafe = replace(SAFE, **{field: False})
    bundle = dossier.assemble_bundle(
        facts=unsafe, git=None, proxy_state="skipped_unsafe_account", now=NOW,
    )
    assert_blocked(bundle)
    assert bundle.git_branch is None and bundle.git_head_metadata_only_untrusted is None
    assert bundle.proxy_socket_metadata == "skipped_unsafe_account"
    assert "HML_HOST_METADATA_SKIPPED_UNSAFE_ACCOUNT" in bundle.blocks
    with pytest.raises(dossier.HMLReviewBundleError, match="HML_REVIEW_UNSAFE_EVIDENCE"):
        dossier.assemble_bundle(
            facts=unsafe, git=META, proxy_state="metadata_only_untrusted", now=NOW,
        )


def test_nnp_and_seccomp_manual_diagnostics_are_not_deploy_gates():
    observed = replace(SAFE, no_new_privileges=False, seccomp_filter=None)
    assert dossier.safe_to_read_metadata(observed) is True
    report = dossier.assemble_bundle(
        facts=observed, git=META, proxy_state="unavailable", now=NOW,
    )
    assert_blocked(report)
    assert "COLLECTOR_NO_NEW_PRIVILEGES_NOT_ESTABLISHED" in report.blocks
    assert "COLLECTOR_SECCOMP_FILTER_NOT_ESTABLISHED" in report.blocks


@pytest.mark.parametrize("state,expected", [
    ("unavailable", "HML_PROXY_UNAVAILABLE"),
    ("unsafe_or_unverifiable", "HML_PROXY_METADATA_UNSAFE_OR_UNVERIFIABLE"),
    ("metadata_only_untrusted", "HML_PROXY_METADATA_ONLY_NOT_ATTESTED"),
])
def test_metadata_status_is_never_independent_policy_attestation(state, expected):
    report = dossier.assemble_bundle(
        facts=SAFE, git=None, proxy_state=state, now=NOW,
    )
    assert expected in report.blocks
    assert report.git_head_metadata_only_untrusted is None
    assert "HML_GIT_METADATA_UNAVAILABLE" in report.blocks
    assert_blocked(report)


@pytest.mark.parametrize("changes", [
    {"checkout_attested": True},
    {"clean_status_observed": True},
    {"challenge_bound": True},
    {"prepare_eligible": True},
    {"can_execute": True},
    {"source": "signed_release"},
    {"head_sha": "z"*40},
    {"head_sha": "A"*40},
    {"head_sha": "a"*39},
    {"branch": "develop"},
])
def test_forged_git_authority_is_rejected(changes):
    with pytest.raises(dossier.HMLReviewBundleError, match="HML_REVIEW_GIT_CONTRACT_INVALID"):
        dossier.assemble_bundle(
            facts=SAFE, git=replace(META, **changes),
            proxy_state="metadata_only_untrusted", now=NOW,
        )


@pytest.mark.parametrize("proxy,now", [
    ("approved", NOW),
    ("", NOW),
    (True, NOW),
    ("unavailable", datetime(2026,11,17,14,0)),
])
def test_wrong_state_or_clock_fails_closed(proxy, now):
    with pytest.raises(dossier.HMLReviewBundleError, match="HML_REVIEW_INPUT_INVALID"):
        dossier.assemble_bundle(facts=SAFE, git=None, proxy_state=proxy, now=now)


def test_safe_collection_is_read_only_and_not_a_docker_connection(monkeypatch):
    seen = {"git": 0, "socket_stat": 0}
    monkeypatch.setattr(dossier, "observe_current_process", lambda: SAFE)
    def peek(_instance):
        seen["git"] += 1
        return META
    def metadata_only():
        seen["socket_stat"] += 1
    monkeypatch.setattr(dossier.GitHeadMetadataPeek, "read", peek)
    monkeypatch.setattr(dossier, "verify_socket_metadata", metadata_only)
    result = dossier.collect_local_bundle()
    assert result.git_head_metadata_only_untrusted == "a"*40
    assert result.proxy_socket_metadata == "metadata_only_untrusted"
    assert seen == {"git": 1, "socket_stat": 1}
    assert result.status == "blocked"
    assert not result.prepare_eligible and not result.can_execute


def test_root_or_docker_user_skips_all_git_and_socket_observations(monkeypatch):
    unsafe = replace(SAFE, named_account_matches_process=False)
    monkeypatch.setattr(dossier, "observe_current_process", lambda: unsafe)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("must not read metadata under an unsafe account")
    monkeypatch.setattr(dossier.GitHeadMetadataPeek, "read", forbidden)
    monkeypatch.setattr(dossier, "verify_socket_metadata", forbidden)
    result = dossier.collect_local_bundle()
    assert result.proxy_socket_metadata == "skipped_unsafe_account"
    assert result.git_head_metadata_only_untrusted is None
    assert "HML_HOST_METADATA_SKIPPED_UNSAFE_ACCOUNT" in result.blocks
    assert not result.can_execute


def test_unavailable_socket_is_observed_without_connecting(monkeypatch):
    monkeypatch.setattr(dossier, "observe_current_process", lambda: SAFE)
    monkeypatch.setattr(dossier.GitHeadMetadataPeek, "read", lambda _: META)
    def unavailable():
        raise HMLUDSPolicyError("HML_PROXY_UNAVAILABLE")
    monkeypatch.setattr(dossier, "verify_socket_metadata", unavailable)
    assert dossier.collect_local_bundle().proxy_socket_metadata == "unavailable"


def test_malformed_socket_or_os_error_is_sanitized(monkeypatch, capsys):
    monkeypatch.setattr(dossier, "observe_current_process", lambda: SAFE)
    monkeypatch.setattr(dossier.GitHeadMetadataPeek, "read", lambda _:
        (_ for _ in ()).throw(RuntimeError("SECRET_GIT_PATH_TEST")))
    monkeypatch.setattr(dossier, "verify_socket_metadata", lambda:
        (_ for _ in ()).throw(PermissionError("SECRET_DOCKER_PATH_TEST")))
    assert dossier.main() == 0
    output = capsys.readouterr().out
    assert "SECRET_" not in output
    report = json.loads(output)
    assert report["status"] == "blocked"
    assert report["git_head_metadata_only_untrusted"] is None
    assert report["proxy_socket_metadata"] == "unsafe_or_unverifiable"
    assert report["can_execute"] is False


def test_fatal_diagnostic_error_is_a_finite_blocked_response(monkeypatch,capsys):
    monkeypatch.setattr(dossier, "observe_current_process", lambda:
        (_ for _ in ()).throw(RuntimeError("CREDENTIAL_TEST_VALUE")))
    assert dossier.main() == 2
    data = capsys.readouterr().out
    assert "CREDENTIAL_TEST_VALUE" not in data
    assert json.loads(data) == {
        "status": "blocked", "code": "HML_REVIEW_BUNDLE_UNAVAILABLE",
        "prepare_eligible": False, "can_execute": False,
    }


def test_bundle_is_fixed_scope_with_no_process_or_mcp_entrypoint():
    assert not hasattr(dossier, "deploy")
    assert not hasattr(dossier, "serve")
    assert not hasattr(dossier, "create_mcp_server")
    assert set(asdict(dossier.assemble_bundle(
        facts=SAFE, git=META, proxy_state="metadata_only_untrusted",
        now=NOW,
    )))["checks"]) == set(CollectorPostureFacts.__dataclass_fields__)
