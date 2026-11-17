"""Disposable, offline negative tests for Architecture B SEC-01..10 index.

There is NO access to real host facts, systemd, Docker, files referenced in
the manifest, Keycloak, MCP or deploy. Every well-formed response is BLOCKED.
"""
from __future__ import annotations

import json
from dataclasses import asdict, replace

import pytest

from linux_ops_mcp import atlas_hml_b_preactivation_evidence as gate

_IDS = tuple(f"SEC-{i:02d}" for i in range(1, 11))


def sample(*, status="PENDENTE") -> dict:
    rows = []
    for i, key in enumerate(_IDS):
        rows.append({
            "id": key,
            "claimed_result": status,
            "origin": (
                "not_provided" if status == "PENDENTE"
                else sorted(gate._ORIGINS[key])[0]
            ),
            "evidence_ref": None if status == "PENDENTE" else f"EVID-TEST{i:04d}AB",
            "sha256": None if status == "PENDENTE" else chr(97 + i) * 64,
        })
    return {
        "schema": gate._SCHEMA,
        "source": "operator_supplied_untrusted",
        "architecture": "B",
        "environment": "hml",
        "compose_project": "delpi-hml",
        "service_id": "public-hub",
        "container_name": "delpi-hml-public-hub",
        "host_claim": "srv-api",
        "checks": rows,
    }


def run(value):
    return gate.review_untrusted_b_preactivation_evidence(
        json.dumps(value, separators=(",", ":"), ensure_ascii=True).encode(),
    )


def denied(code, fn):
    with pytest.raises(gate.HMLBPreactivationEvidenceError) as exc:
        fn()
    assert exc.value.code == code
    assert str(exc.value) == code


def must_remain_blocked(result):
    assert result.status == "blocked"
    assert result.architecture == "B"
    assert result.environment == "hml"
    assert result.service_id == "public-hub"
    assert result.rows_reviewed == 10
    assert result.source == "operator_supplied_untrusted"
    assert not result.independent_human_attestation
    assert not result.host_isolation_attested
    assert not result.privileged_producer_attested
    assert not result.rollback_attested
    assert not result.operational_authorization_granted
    assert not result.prepare_eligible
    assert not result.can_execute
    assert "HML_B_EVIDENCE_INDEX_IS_UNTRUSTED" in result.blocks
    assert "HML_B_DOCKER_PRODUCER_RETAINS_HOST_EQUIVALENT_RISK" in result.blocks
    assert "HML_B_SEC01_INDEPENDENT_HUMAN_REVIEW_NOT_ATTESTED" in result.blocks
    assert "HML_B_OPERATIONAL_CHANGE_NOT_AUTHORIZED" in result.blocks
    assert "PREPARE_DISABLED" in result.blocks
    assert "ACT_DISABLED" in result.blocks


def test_empty_matrix_is_pending_and_never_eligible():
    report = run(sample())
    must_remain_blocked(report)
    assert report.pending_items == _IDS
    assert report.claimed_complete_items == ()
    assert report.rejected_items == ()
    assert report.claimed_governance_exception is False
    assert len([x for x in report.blocks if x.endswith("_PENDING")]) == 10


def test_all_ten_claimed_comprovado_is_still_untrusted_and_blocked():
    report = run(sample(status="COMPROVADO"))
    must_remain_blocked(report)
    assert report.claimed_complete_items == _IDS
    assert report.pending_items == ()
    assert "HML_B_ALL_CLAIMS_SUBMITTED_BUT_NOT_ATTESTED" in report.blocks
    assert report.independent_human_attestation is False
    assert report.operational_authorization_granted is False


def test_governance_exception_claim_never_becomes_independent_human_review():
    document = sample(status="COMPROVADO")
    document["checks"][0]["origin"] = "governance_exception_claim"
    report = run(document)
    must_remain_blocked(report)
    assert report.claimed_governance_exception
    assert "HML_B_SEC01_GOVERNANCE_EXCEPTION_UNVERIFIED" in report.blocks
    assert not report.independent_human_attestation


def test_reported_rejection_remains_blocked_without_reflecting_reference():
    document = sample(status="COMPROVADO")
    document["checks"][2]["claimed_result"] = "REPROVADO"
    report = run(document)
    must_remain_blocked(report)
    assert report.rejected_items == ("SEC-03",)
    assert "HML_B_SEC_03_REJECTED_CLAIM" in report.blocks
    assert "EVID-TEST0002AB" not in repr(report)


def test_partial_evidence_never_promotes_preparation():
    document = sample()
    document["checks"][1] = sample(status="COMPROVADO")["checks"][1]
    report = run(document)
    must_remain_blocked(report)
    assert report.claimed_complete_items == ("SEC-02",)
    assert "HML_B_SEC_01_PENDING" in report.blocks


@pytest.mark.parametrize("field,bad", [
    ("schema", "atlas.hml.architecture-b.preactivation-evidence.v2"),
    ("source", "independent_signed_attestation"),
    ("architecture", "A"),
    ("architecture", "C"),
    ("environment", "prod"),
    ("compose_project", "delpi-prod"),
    ("service_id", "db"),
    ("container_name", "delpi-public-hub"),
    ("host_claim", "some-other-host"),
    ("host_claim", True),
    ("service_id", 7),
])
def test_wrong_fixed_scope_is_denied(field, bad):
    document = sample()
    document[field] = bad
    denied("HML_B_EVIDENCE_SCOPE_INVALID", lambda: run(document))


@pytest.mark.parametrize("extra", [
    {"can_execute": True},
    {"prepare_eligible": True},
    {"status": "approved"},
    {"operational_authorization_granted": True},
    {"docker_access_attested": True},
    {"custom_script": "systemctl restart docker"},
])
def test_extra_authority_claims_are_not_in_manifest(extra):
    document = sample()
    document.update(extra)
    denied("HML_B_EVIDENCE_SCOPE_INVALID", lambda: run(document))


def test_missing_scope_field_is_denied():
    document = sample()
    del document["architecture"]
    denied("HML_B_EVIDENCE_SCOPE_INVALID", lambda: run(document))


@pytest.mark.parametrize("bad", [None, {}, [], "wrong", True])
def test_bad_matrix_shape_is_denied(bad):
    document = sample()
    document["checks"] = bad
    denied("HML_B_EVIDENCE_MATRIX_INVALID", lambda: run(document))


def test_missing_or_duplicate_sec_item_is_denied():
    document = sample()
    document["checks"][5] = dict(document["checks"][4])
    denied("HML_B_EVIDENCE_ROW_INVALID", lambda: run(document))
    document = sample()
    document["checks"].pop()
    denied("HML_B_EVIDENCE_MATRIX_INVALID", lambda: run(document))


@pytest.mark.parametrize("mutation,code", [
    ({"id": "SEC-11"}, "HML_B_EVIDENCE_ROW_INVALID"),
    ({"id": "sec-01"}, "HML_B_EVIDENCE_ROW_INVALID"),
    ({"id": 1}, "HML_B_EVIDENCE_ROW_INVALID"),
    ({"claimed_result": "APROVADO"}, "HML_B_EVIDENCE_ROW_INVALID"),
    ({"claimed_result": True}, "HML_B_EVIDENCE_ROW_INVALID"),
    ({"origin": False}, "HML_B_EVIDENCE_ROW_INVALID"),
    ({"origin": "ci_disposable"}, "HML_B_EVIDENCE_PENDING_CONTRADICTION"),
    ({"evidence_ref": "EVID-ABCDEFGHI"}, "HML_B_EVIDENCE_PENDING_CONTRADICTION"),
    ({"sha256": "a" * 64}, "HML_B_EVIDENCE_PENDING_CONTRADICTION"),
])
def test_invalid_or_contradictory_pending_row_is_denied(mutation, code):
    document = sample()
    document["checks"][0].update(mutation)
    denied(code, lambda: run(document))


def test_extra_row_authority_claim_and_missing_field_are_denied():
    for change in ("add", "remove"):
        document = sample()
        if change == "add":
            document["checks"][0]["host_approved"] = True
        else:
            del document["checks"][0]["origin"]
        denied("HML_B_EVIDENCE_ROW_INVALID", lambda: run(document))


@pytest.mark.parametrize("key,bad", [
    ("origin", "ci_disposable"),
    ("origin", "not_provided"),
    ("origin", "human_independent_claim"),
    ("evidence_ref", "/etc/shadow"),
    ("evidence_ref", "../unsafe"),
    ("evidence_ref", ""),
    ("evidence_ref", None),
    ("evidence_ref", True),
    ("sha256", "A" * 64),
    ("sha256", "a" * 63),
    ("sha256", ""),
    ("sha256", None),
    ("sha256", True),
])
def test_claimed_host_gate_requires_strict_metadata_and_host_provenance(key, bad):
    document = sample(status="COMPROVADO")
    document["checks"][2][key] = bad
    denied("HML_B_EVIDENCE_PROVENANCE_UNVERIFIABLE", lambda: run(document))


def test_ci_evidence_cannot_be_forged_as_real_sec03_isolation():
    document = sample(status="COMPROVADO")
    document["checks"][2]["origin"] = "ci_disposable"
    denied("HML_B_EVIDENCE_PROVENANCE_UNVERIFIABLE", lambda: run(document))


def test_duplicate_references_do_not_count_as_two_independent_items():
    document = sample(status="COMPROVADO")
    document["checks"][3]["evidence_ref"] = document["checks"][2]["evidence_ref"]
    denied("HML_B_EVIDENCE_PROVENANCE_UNVERIFIABLE", lambda: run(document))


def test_input_order_cannot_drop_a_gate():
    document = sample()
    document["checks"].reverse()
    report = run(document)
    must_remain_blocked(report)
    assert report.pending_items == _IDS


@pytest.mark.parametrize("raw,code", [
    (b"", "HML_B_EVIDENCE_INPUT_INVALID"),
    (b"\x00", "HML_B_EVIDENCE_INPUT_INVALID"),
    (b" " * 12289, "HML_B_EVIDENCE_INPUT_INVALID"),
    ("not-bytes", "HML_B_EVIDENCE_INPUT_INVALID"),
    (b"{", "HML_B_EVIDENCE_JSON_INVALID"),
    (b"\xff", "HML_B_EVIDENCE_JSON_INVALID"),
    (b'{"x":NaN}', "HML_B_EVIDENCE_JSON_INVALID"),
    (b'{"x":Infinity}', "HML_B_EVIDENCE_JSON_INVALID"),
    (b'{"x":1,"x":2}', "HML_B_EVIDENCE_DUPLICATE_JSON_FIELD"),
])
def test_malformed_payload_is_sanitized_and_fail_closed(raw, code):
    denied(code, lambda: gate.review_untrusted_b_preactivation_evidence(raw))


def test_duplicate_json_key_nested_inside_sec_item_rejected():
    raw = json.dumps(sample()).replace(
        '"claimed_result": "PENDENTE"',
        '"claimed_result": "PENDENTE", "claimed_result": "COMPROVADO"',
        1,
    ).encode()
    denied("HML_B_EVIDENCE_DUPLICATE_JSON_FIELD", lambda:
           gate.review_untrusted_b_preactivation_evidence(raw))


def test_manifest_does_not_reveal_refs_or_digests():
    document = sample(status="COMPROVADO")
    observed = run(document)
    result = asdict(observed)
    must_remain_blocked(observed)
    assert "EVID-" not in json.dumps(result)
    assert "sha256" not in result
    assert "origin" not in result
    assert "SEC-01" in observed.claimed_complete_items


def test_bad_type_and_forged_result_does_not_mutate_original():
    result = run(sample(status="COMPROVADO"))
    promoted = replace(result, can_execute=True)
    assert result.can_execute is False
    assert promoted.can_execute is True  # user-created dataclass is not attestation.
    # The real parser cannot accept a request to promote a flag.
    document = sample(status="COMPROVADO")
    document["can_execute"] = True
    denied("HML_B_EVIDENCE_SCOPE_INVALID", lambda: run(document))


def test_review_module_has_no_runtime_or_docker_side_effect_entrypoint():
    for name in (
        "main", "deploy", "serve", "connect", "install", "start_service",
        "create_mcp_server", "collect_local_bundle", "docker_client",
    ):
        assert not hasattr(gate, name)
    assert not hasattr(gate, "httpx")
    assert not hasattr(gate, "subprocess")
    assert not hasattr(gate, "socket")
