"""Negative tests for ATLAS 64 offline preactivation dossier."""
import json
import pytest

from linux_ops_mcp.atlas_hml_b_stage64_review import (
    HMLStage64ReviewError, review_untrusted_stage64_dossier,
)

_KEYS = (
    "owner_change_record", "independent_security_decision", "real_host_baseline",
    "docker_aliases_and_inherited_fds", "systemd_effective_units",
    "uid_gid_acl_capabilities_lsm", "socket_peer_authentication",
    "signer_bootstrap_anchor", "key_custody_escrow", "hml_negative_tests",
    "prod_unchanged_baseline", "atlas_only_rollback", "change_window",
)


def dossier():
    return {
        "schema": "atlas.hml.b.preactivation-v1",
        "host": "srv-api", "environment": "hml",
        "target": "delpi-hml-public-hub",
        "revision_sha": "c" * 40,
        "source": "untrusted_manual_evidence_index",
        "systemd_installed": False, "key_generated": False,
        "mcp_tools": [
            "get_deployment_revision", "get_host_health",
            "get_service_health", "list_managed_services",
        ],
        "prepare_enabled": False, "act_enabled": False,
        "roles": {
            "producer": "root", "bridge": "atlas-hml-bridge",
            "signer": "atlas-hml-signer", "presenter": "atlas-hml",
        },
        "evidence": dict.fromkeys(_KEYS, "missing"),
    }


def review(d):
    return review_untrusted_stage64_dossier(
        json.dumps(d, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def assert_denied(d):
    with pytest.raises(HMLStage64ReviewError):
        review(d)


def test_everything_missing_remains_blocked():
    out = review(dossier())
    assert out.status == "blocked"
    assert out.evidence_items == 13 and out.declared_present == 0
    assert out.can_execute is False and out.prepare_eligible is False
    assert out.host_attested is False and out.owner_authorization_granted is False


def test_all_evidence_declared_does_not_grant_permission():
    d = dossier()
    d["evidence"] = dict.fromkeys(_KEYS, "declared_present_untrusted")
    out = review(d)
    assert out.declared_present == 13
    assert not out.host_attested and not out.signer_bootstrap_approved
    assert not out.systemd_installed and not out.can_execute


@pytest.mark.parametrize("field,value", [
    ("environment", "prod"), ("target", "delpi-public-hub"),
    ("host", "other-host"), ("source", "approved_by_owner"),
    ("systemd_installed", True), ("key_generated", True),
    ("prepare_enabled", True), ("act_enabled", True),
    ("revision_sha", "main"), ("revision_sha", "C" * 40),
])
def test_scope_and_activation_denied(field, value):
    d = dossier()
    d[field] = value
    assert_denied(d)


def test_root_bridge_and_docker_group_denied():
    for group in ("root", "docker", "atlas-hml-bridge docker"):
        d = dossier()
        d["roles"]["bridge"] = group
        assert_denied(d)


def test_root_signer_denied():
    d = dossier()
    d["roles"]["signer"] = "root"
    assert_denied(d)


def test_extra_and_missing_evidence_denied():
    for edit in ("extra", "missing"):
        d = dossier()
        if edit == "extra":
            d["evidence"]["prod_deployment"] = "declared_present_untrusted"
        else:
            del d["evidence"]["signer_bootstrap_anchor"]
        assert_denied(d)


def test_evidence_cannot_claim_verified():
    d = dossier()
    d["evidence"]["real_host_baseline"] = "attested"
    assert_denied(d)


def test_extra_fields_and_tool_expansion_denied():
    d = dossier()
    d["run_shell"] = False
    assert_denied(d)
    d = dossier()
    d["mcp_tools"].append("deploy")
    assert_denied(d)


@pytest.mark.parametrize("raw", [
    b'{"schema":1,"schema":2}',
    b'{"x":NaN}', b'null', b'[]', b'',
    b'\x00', b'{' + b'a' * 16385,
])
def test_malformed_denied(raw):
    with pytest.raises(HMLStage64ReviewError):
        review_untrusted_stage64_dossier(raw)


def test_json_boolean_or_numeric_not_accepted_as_roles_evidence():
    d = dossier()
    d["roles"]["producer"] = 1
    assert_denied(d)
    d = dossier()
    d["evidence"]["change_window"] = True
    assert_denied(d)
