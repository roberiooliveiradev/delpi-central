"""ATLAS P2.2h.2k: real HMAC signing/verification; hermetic Docker fixture.

No production access, no POST, no PostgreSQL writes, no Core or ACT.
Even an otherwise consistent signed receipt must never become eligible.
"""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from linux_ops_mcp.deploy_host_oci_preflight import (
    HostOCIIntentPreview,
    HostOCIPreflightError,
    inspect_host_oci_preflight_v2,
)
from linux_ops_mcp.deploy_host_receipt import SignedHostReceipt
from linux_ops_mcp.deploy_host_runtime_v2 import issue_host_runtime_receipt_v2
from linux_ops_mcp.deploy_host_signer import SignedReleaseRecord, _DOMAIN as RELEASE_DOMAIN
from linux_ops_mcp.deploy_host_source import RuntimeContainer, RuntimeTarget

NOW = datetime(2026, 11, 16, 22, 0, tzinfo=timezone.utc)
TARGET = RuntimeTarget(
    environment="hml", service_id="public-hub", host_id="srv-api-pilot",
    compose_project="delpi-hml", container_name="delpi-hml-public-hub",
)
BASE_SHA = "a" * 40
TARGET_SHA = "b" * 40
BASE_IMAGE = "sha256:" + "c" * 64
TARGET_IMAGE = "sha256:" + "d" * 64
MANIFEST = "sha256:" + "e" * 64
CHALLENGE = "f" * 64
NONCE_DIGEST = hashlib.sha256(bytes.fromhex(CHALLENGE)).hexdigest()
RELEASE_KEY = b"ephemeral-only-executor-release-seal-key-123456"
HOST_KEY = b"ephemeral-only-host-witness-key-9876543210"


class DockerFixture:
    def __init__(self, *, image=BASE_IMAGE, running=True, healthy=True):
        self.image = image
        self.running = running
        self.healthy = healthy
        self.calls = []

    async def inspect(self, target):
        self.calls.append(target)
        return RuntimeContainer(
            container_id="1" * 64, image_id=self.image,
            running=self.running, healthy=self.healthy,
        )


def signed_record(target=TARGET):
    data = {
        "version": 1, "repository": "roberiooliveiradev/delpi-central",
        "host_id": target.host_id, "environment": target.environment,
        "service_id": target.service_id, "execution_id": str(uuid4()),
        "commit_sha": BASE_SHA, "image_id": BASE_IMAGE,
    }
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return SignedReleaseRecord(
        raw, hmac.new(RELEASE_KEY, RELEASE_DOMAIN + raw, hashlib.sha256).hexdigest(),
    )


def signed_receipt(*, target=TARGET, inspector=None, challenge=CHALLENGE, observed=NOW):
    return asyncio.run(issue_host_runtime_receipt_v2(
        target=target, release_record=signed_record(target),
        inspector=inspector or DockerFixture(), release_key=RELEASE_KEY,
        host_key=HOST_KEY, challenge=challenge, now=observed,
    ))


def expected(**changes):
    return replace(HostOCIIntentPreview(
        environment="hml", service_id="public-hub",
        base_commit_sha=BASE_SHA, base_image_id=BASE_IMAGE,
        target_commit_sha=TARGET_SHA, target_image_id=TARGET_IMAGE,
        manifest_digest=MANIFEST,
        attestation_statement_sha256="2" * 64,
        host_challenge_sha256=NONCE_DIGEST,
        rollback_image_id=BASE_IMAGE,
        rollback_ready=True,
    ), **changes)


def run_check(*, receipt=None, intent=None, target=TARGET,
              challenge=CHALLENGE, host_key=HOST_KEY, now=NOW):
    return inspect_host_oci_preflight_v2(
        signed_receipt=receipt if receipt is not None else signed_receipt(),
        host_key=host_key, target=target, expected_challenge=challenge,
        intent=intent if intent is not None else expected(), now=now,
    )


def reject(code, **kwargs):
    with pytest.raises(HostOCIPreflightError) as caught:
        run_check(**kwargs)
    assert caught.value.code == code
    assert CHALLENGE not in str(caught.value)
    assert HOST_KEY.decode() not in str(caught.value)


def test_exact_match_never_grants_prepare_even_with_valid_mac_and_health():
    docker = DockerFixture()
    proof = signed_receipt(inspector=docker)
    result = run_check(receipt=proof)
    assert docker.calls == [TARGET]
    assert result.status == "blocked"
    assert result.blocks == (
        "OCI_CI_RELEASE_NOT_REVERIFIED",
        "OCI_CHECKOUT_NOT_ATTESTED",
        "OCI_MIGRATIONS_NOT_ATTESTED",
        "OCI_ROLLBACK_NOT_ATTESTED",
        "OCI_CHALLENGE_NOT_CONSUMED",
        "OCI_CORE_AUTHORIZATION_MISSING",
    )
    assert result.observed_base_commit_sha == BASE_SHA
    assert result.observed_base_image_id == BASE_IMAGE
    assert result.challenge_sha256 == NONCE_DIGEST
    assert result.signed_receipt_sha256 == hashlib.sha256(proof.body).hexdigest()
    assert result.environment == "hml" and result.service_id == "public-hub"
    assert result.observed_at == NOW
    assert not hasattr(result, "candidate")
    assert not hasattr(result, "approved")
    assert not hasattr(result, "can_act")


@pytest.mark.parametrize("field,value,reason", [
    ("base_commit_sha", "0" * 40, "OCI_BASE_COMMIT_DRIFT"),
    ("base_image_id", "sha256:" + "0" * 64, "OCI_BASE_IMAGE_DRIFT"),
    ("target_commit_sha", BASE_SHA, "OCI_TARGET_ALREADY_DEPLOYED"),
    ("target_image_id", BASE_IMAGE, "OCI_TARGET_IMAGE_UNCHANGED"),
    ("rollback_image_id", "sha256:" + "0" * 64, "OCI_ROLLBACK_IDENTITY_DRIFT"),
    ("rollback_ready", False, "OCI_ROLLBACK_INTENT_UNREADY"),
])
def test_signed_host_never_overrides_inconsistent_oci_intent(field, value, reason):
    report = run_check(intent=expected(**{field: value}))
    assert report.status == "blocked"
    assert reason in report.blocks
    assert "OCI_CHALLENGE_NOT_CONSUMED" in report.blocks


def test_unhealthy_or_stopped_docker_is_reported_and_not_authorized():
    for running, healthy in ((True, False), (False, True), (False, False)):
        proof = signed_receipt(inspector=DockerFixture(running=running, healthy=healthy))
        report = run_check(receipt=proof)
        assert "OCI_HOST_NOT_HEALTHY" in report.blocks


@pytest.mark.parametrize("field,invalid", [
    ("base_commit_sha", "main"),
    ("target_commit_sha", "A" * 40),
    ("base_image_id", "sha256:short"),
    ("target_image_id", "sha256:" + "A" * 64),
    ("manifest_digest", "latest"),
    ("attestation_statement_sha256", "BAD"),
    ("host_challenge_sha256", None),
    ("rollback_image_id", None),
    ("rollback_ready", 1),
])
def test_invalid_preview_inputs_denied_before_any_trust_claim(field, invalid):
    reject("OCI_PREFLIGHT_INTENT_INVALID", intent=expected(**{field: invalid}))


def test_intent_wrong_environment_or_service_is_denied_before_signature():
    reject("OCI_PREFLIGHT_INTENT_TARGET_DRIFT", intent=expected(environment="prod"))
    reject("OCI_PREFLIGHT_INTENT_TARGET_DRIFT", intent=expected(service_id="other"))


@pytest.mark.parametrize("changes,code", [
    ({"container_name": "another-container"}, "OCI_PREFLIGHT_TARGET_NOT_ALLOWLISTED"),
    ({"compose_project": "another-project"}, "OCI_PREFLIGHT_TARGET_NOT_ALLOWLISTED"),
    ({"service_id": "mysql"}, "OCI_PREFLIGHT_TARGET_NOT_ALLOWLISTED"),
    ({"environment": "test"}, "OCI_PREFLIGHT_TARGET_INVALID"),
])
def test_pilot_allowlist_rejects_wrong_runtime_target(changes, code):
    target = replace(TARGET, **changes)
    reject(code, target=target)


def test_host_mac_rejects_wrong_key_or_modified_receipt():
    original = signed_receipt()
    reject(
        "OCI_PREFLIGHT_HOST_HOST_V2_SIGNATURE_INVALID",
        receipt=SignedHostReceipt(original.body + b" ", original.mac_hex),
    )
    reject(
        "OCI_PREFLIGHT_HOST_HOST_V2_SIGNATURE_INVALID",
        receipt=original,
        host_key=b"wrong-secret-for-another-host-000001",
    )


def test_replayed_nonce_under_new_challenge_is_rejected_without_db_consumption():
    different = "a" * 64
    changed_digest = hashlib.sha256(bytes.fromhex(different)).hexdigest()
    # Reject as early as the hash expected by the journal mismatches.
    reject(
        "OCI_PREFLIGHT_CHALLENGE_DIGEST_DRIFT",
        challenge=different,
    )
    # Even if caller forges intent's hash to match the new challenge,
    # the signed host receipt still ties its MAC to the original nonce.
    reject(
        "OCI_PREFLIGHT_HOST_HOST_V2_TARGET_MISMATCH",
        challenge=different,
        intent=expected(host_challenge_sha256=changed_digest),
    )


def test_db_nonce_hash_convention_is_bytes_not_ascii_text():
    ascii_digest = hashlib.sha256(CHALLENGE.encode("ascii")).hexdigest()
    assert ascii_digest != NONCE_DIGEST
    reject(
        "OCI_PREFLIGHT_CHALLENGE_DIGEST_DRIFT",
        intent=expected(host_challenge_sha256=ascii_digest),
    )


def test_host_target_drift_is_denied_by_mac_bound_receipt():
    drifted = RuntimeTarget(
        environment="prod", service_id="public-hub", host_id=TARGET.host_id,
        compose_project="infra", container_name="delpi-public-hub",
    )
    prod_intent = expected(environment="prod")
    reject(
        "OCI_PREFLIGHT_HOST_HOST_V2_TARGET_MISMATCH",
        receipt=signed_receipt(), intent=prod_intent, target=drifted,
    )


def test_release_record_ensures_image_is_same_as_docker_inspect():
    # The signer refuses to produce a receipt for another running ImageID.
    from linux_ops_mcp.deploy_host_signer import HostSigningError
    with pytest.raises(HostSigningError, match="RUNNING_IMAGE_NOT_APPROVED"):
        signed_receipt(inspector=DockerFixture(image="sha256:" + "0" * 64))


def test_signed_receipt_freshness_is_checked_again_in_the_preflight():
    original = signed_receipt()
    reject(
        "OCI_PREFLIGHT_HOST_HOST_V2_OBSERVATION_STALE",
        receipt=original,
        now=NOW + timedelta(seconds=91),
    )
    reject(
        "OCI_PREFLIGHT_HOST_HOST_V2_OBSERVATION_STALE",
        receipt=original,
        now=NOW - timedelta(seconds=6),
    )


@pytest.mark.parametrize("now", [
    NOW.replace(tzinfo=None), None, "today",
])
def test_clock_invalid_is_rejected_before_mac(now):
    reject("OCI_PREFLIGHT_CLOCK_INVALID", now=now)


@pytest.mark.parametrize("challenge", [
    "bad", "0" * 63, "A" * 64, None,
])
def test_challenge_invalid_is_rejected_before_mac(challenge):
    reject("OCI_PREFLIGHT_CHALLENGE_INVALID", challenge=challenge)


def test_valid_receipt_cannot_be_used_to_prove_missing_safety_gates():
    report = run_check()
    assert report.status == "blocked"
    assert set((
        "OCI_CI_RELEASE_NOT_REVERIFIED",
        "OCI_CHECKOUT_NOT_ATTESTED",
        "OCI_MIGRATIONS_NOT_ATTESTED",
        "OCI_ROLLBACK_NOT_ATTESTED",
        "OCI_CHALLENGE_NOT_CONSUMED",
        "OCI_CORE_AUTHORIZATION_MISSING",
    )).issubset(set(report.blocks))
    assert "ready" not in vars(type(report)).get("__dict__", {})
    assert "approved" not in report.status


def test_no_new_endpoints_or_mutating_commands_in_module():
    from pathlib import Path

    file = (
        Path(__file__).resolve().parents[1]
        / "linux_ops_mcp/deploy_host_oci_preflight.py"
    )
    source = file.read_text()
    for forbidden in (
        "@router.", "docker compose", "os.system", "subprocess.run",
        "psycopg.connect", "execute(", "CREATE TABLE",
    ):
        assert forbidden not in source
