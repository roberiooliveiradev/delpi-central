"""Untrusted offline observation tests; no live host discovery."""
import json

import pytest

from linux_ops_mcp.atlas_hml_b_process_evidence import (
    HMLProcessEvidenceError, review_untrusted_process_observation,
)

BASE = {
    "schema": "atlas.hml.b.process-observation.v1",
    "source": "operator_supplied_untrusted",
    "host": "srv-api",
    "role": "presenter",
    "uid": 995, "euid": 995, "gid": 985, "egid": 985,
    "supplementary_gids": [],
    "cap_eff": "0000000000000000", "cap_prm": "0000000000000000",
    "cap_amb": "0000000000000000",
    "no_new_privileges": True, "seccomp_mode": 2,
    "lsm_enforcing": True, "namespace_isolation_verified": True,
    "fd_targets": ["socket:[1234]"],
    "docker_endpoints_checked": [
        "/run/docker.sock", "/var/run/docker.sock", "docker_tcp",
        "docker_host_env", "docker_fd_inheritance", "docker_mount_aliases",
    ],
    "evidence_sha256": "a" * 64,
}


def inspect(data):
    return review_untrusted_process_observation(json.dumps(data).encode())


def test_review_is_never_operational_attestation():
    x = inspect(BASE)
    assert x.status == "blocked" and not x.can_execute
    assert not x.host_attested and not x.producer_attested
    assert not x.prepare_eligible and "ACT_DISABLED" in x.blocks


@pytest.mark.parametrize("patch,code", [
    ({"host": "other"}, "HML_PROCESS_SCOPE_DENIED"),
    ({"role": "producer"}, "HML_PROCESS_SCOPE_DENIED"),
    ({"uid": 0}, "HML_PROCESS_IDENTITY_DENIED"),
    ({"euid": 0}, "HML_PROCESS_IDENTITY_DENIED"),
    ({"supplementary_gids": [999]}, "HML_PROCESS_GROUPS_DENIED"),
    ({"cap_eff": "0000000000000001"}, "HML_PROCESS_CAPABILITIES_DENIED"),
    ({"no_new_privileges": False}, "HML_PROCESS_SANDBOX_UNVERIFIED"),
    ({"seccomp_mode": 0}, "HML_PROCESS_SANDBOX_UNVERIFIED"),
    ({"lsm_enforcing": False}, "HML_PROCESS_SANDBOX_UNVERIFIED"),
    ({"namespace_isolation_verified": False}, "HML_PROCESS_SANDBOX_UNVERIFIED"),
    ({"fd_targets": ["socket:[1234]", "socket:[4321]"]}, "HML_PROCESS_FD_UNVERIFIED"),
    ({"fd_targets": ["/run/docker.sock"]}, "HML_PROCESS_FD_UNVERIFIED"),
    ({"docker_endpoints_checked": ["docker_tcp"]}, "HML_PROCESS_ENDPOINTS_UNVERIFIED"),
    ({"evidence_sha256": "not a digest"}, "HML_PROCESS_EVIDENCE_UNVERIFIED"),
    ({"can_execute": True}, "HML_PROCESS_INVALID_SCHEMA"),
])
def test_negative_fixtures(patch, code):
    with pytest.raises(HMLProcessEvidenceError) as exc:
        inspect({**BASE, **patch})
    assert exc.value.code == code


def test_duplicate_json_field_rejected():
    raw = json.dumps(BASE).replace('"uid": 995', '"uid": 995, "uid": 995')
    with pytest.raises(HMLProcessEvidenceError) as exc:
        review_untrusted_process_observation(raw.encode())
    assert exc.value.code == "HML_PROCESS_DUPLICATE_FIELD"


@pytest.mark.parametrize("raw", [b"", b"{" * 4100, b'{"uid":NaN}', b"\x00"])
def test_malformed_input_denied(raw):
    with pytest.raises(HMLProcessEvidenceError):
        review_untrusted_process_observation(raw)
