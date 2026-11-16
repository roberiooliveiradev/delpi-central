"""P2.2h.2j: isolated signed host receipt v2 proof and negative gates.

No real host, Docker socket, GitHub, DB, secret provisioning or deploy.
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

from linux_ops_mcp.deploy_host_receipt import SignedHostReceipt
from linux_ops_mcp.deploy_host_runtime_v2 import (
    HostRuntimeV2Error, VerifiedHostRuntimeSnapshot,
    _DOMAIN, issue_host_runtime_receipt_v2,
    verify_host_runtime_receipt_v2,
)
from linux_ops_mcp.deploy_host_signer import (
    HostSigningError, SignedReleaseRecord, _DOMAIN as RELEASE_DOMAIN,
    issue_host_receipt,
)
from linux_ops_mcp.deploy_host_source import (
    HostSourceError, RuntimeContainer, RuntimeTarget,
)

NOW = datetime(2026, 11, 16, 19, 0, tzinfo=timezone.utc)
TARGET = RuntimeTarget(
    environment="hml", service_id="public-hub", host_id="srv-api-pilot",
    compose_project="delpi-hml", container_name="delpi-hml-public-hub",
)
RELEASE_KEY = b"isolated-executor-release-key-over-32-bytes-test"
HOST_KEY = b"isolated-runtime-host-key-over-32-bytes-test"
CHALLENGE = "a" * 64
IMAGE = "sha256:" + "c" * 64
COMMIT = "d" * 40


class Inspect:
    def __init__(self, *, image=IMAGE, running=True, healthy=True, fail=False):
        self.calls = []
        self.image = image
        self.running = running
        self.healthy = healthy
        self.fail = fail

    async def inspect(self, target):
        self.calls.append(target)
        if self.fail:
            raise HostSourceError("INSPECT_UNAVAILABLE")
        return RuntimeContainer(
            container_id="e" * 64,
            image_id=self.image,
            running=self.running,
            healthy=self.healthy,
        )


def release_record(*, image=IMAGE, target=TARGET):
    body = json.dumps({
        "version": 1, "repository": "roberiooliveiradev/delpi-central",
        "host_id": target.host_id,
        "environment": target.environment,
        "service_id": target.service_id,
        "execution_id": str(uuid4()),
        "commit_sha": COMMIT, "image_id": image,
    }, separators=(",", ":"), sort_keys=True).encode()
    mac = hmac.new(RELEASE_KEY, RELEASE_DOMAIN + body, hashlib.sha256).hexdigest()
    return SignedReleaseRecord(body, mac)


def sign(*, target=TARGET, inspector=None, record=None, challenge=CHALLENGE,
         now=NOW, release_key=RELEASE_KEY, host_key=HOST_KEY):
    return asyncio.run(issue_host_runtime_receipt_v2(
        target=target,
        release_record=record or release_record(target=target),
        inspector=inspector or Inspect(),
        release_key=release_key,
        host_key=host_key,
        challenge=challenge, now=now,
    ))


def verified(receipt, *, target=TARGET, challenge=CHALLENGE, secret=HOST_KEY,
             now=NOW):
    return verify_host_runtime_receipt_v2(
        receipt, target=target, expected_challenge=challenge,
        secret=secret, now=now,
    )


def expect_rejection(receipt, code, **kwargs):
    with pytest.raises(HostRuntimeV2Error) as exc:
        verified(receipt, **kwargs)
    assert exc.value.code == code
    assert CHALLENGE not in str(exc.value)
    assert HOST_KEY.decode() not in str(exc.value)


def resign(fields):
    # Test-only forged MAC, simulates a compromised signer. The verifier must
    # STILL deny unsupported checkout/migration/rollback assertions.
    data = json.dumps(fields, separators=(",", ":"), sort_keys=True).encode()
    mac = hmac.new(HOST_KEY, _DOMAIN + data, hashlib.sha256).hexdigest()
    return SignedHostReceipt(data, mac)


def test_real_signer_path_binds_exact_host_container_project_and_nonce():
    inspector = Inspect()
    receipt = sign(inspector=inspector)
    payload = json.loads(receipt.body)
    assert inspector.calls == [TARGET]
    assert payload["version"] == 2
    assert payload["container_name"] == TARGET.container_name
    assert payload["compose_project"] == TARGET.compose_project
    assert payload["checkout_clean"] is False
    assert len(receipt.mac_hex) == 64
    snapshot = verified(receipt)
    assert type(snapshot) is VerifiedHostRuntimeSnapshot
    assert (snapshot.host_id, snapshot.environment, snapshot.service_id) == (
        TARGET.host_id, TARGET.environment, TARGET.service_id,
    )
    assert (snapshot.container_name, snapshot.compose_project) == (
        TARGET.container_name, TARGET.compose_project,
    )
    assert (snapshot.deployed_commit_sha, snapshot.running_image_id) == (COMMIT, IMAGE)
    assert snapshot.container_id == "e" * 64
    assert snapshot.observed_at == NOW
    assert snapshot.challenge_sha256 == hashlib.sha256(
        bytes.fromhex(CHALLENGE),
    ).hexdigest()
    assert snapshot.signed_receipt_sha256 == hashlib.sha256(receipt.body).hexdigest()
    assert snapshot.running and snapshot.healthy
    assert snapshot.signature_verified and snapshot.challenge_bound
    assert not snapshot.checkout_clean
    assert not snapshot.migrations_safe
    assert not snapshot.rollback_ready
    assert not snapshot.challenge_consumed
    assert not hasattr(snapshot, "release_approved")


@pytest.mark.parametrize("attr,wrong", [
    ("host_id", "other-host"),
    ("environment", "prod"),
    ("service_id", "other-service"),
    ("container_name", "other-container"),
    ("compose_project", "other-compose-project"),
])
def test_target_drift_denied_even_with_valid_host_mac(attr, wrong):
    receipt = sign()
    expect_rejection(receipt, "HOST_V2_TARGET_MISMATCH", target=replace(TARGET, **{attr: wrong}))


def test_nonmatching_challenge_is_denied_and_nonce_is_never_consumed():
    receipt = sign()
    expect_rejection(receipt, "HOST_V2_TARGET_MISMATCH", challenge="b" * 64)
    assert "challenge_consumed" not in receipt.body.decode()


def test_bad_host_key_and_modified_signed_bytes_are_rejected():
    receipt = sign()
    expect_rejection(receipt, "HOST_V2_SIGNATURE_INVALID",
          secret=b"wrong-32-plus-byte-secret-from-another-host")
    expect_rejection(SignedHostReceipt(receipt.body + b" ", receipt.mac_hex),
          "HOST_V2_SIGNATURE_INVALID")


def test_v1_receipt_signature_cannot_be_replayed_as_v2():
    original = asyncio.run(issue_host_receipt(
        target=TARGET, release_record=release_record(), inspector=Inspect(),
        release_key=RELEASE_KEY, host_key=HOST_KEY,
        challenge=CHALLENGE, now=NOW,
    ))
    expect_rejection(original, "HOST_V2_SIGNATURE_INVALID")
    # Even a forged v2-domain MAC on v1 content cannot pass the schema.
    forged = resign(json.loads(original.body))
    expect_rejection(forged, "HOST_V2_RECEIPT_INVALID")


def test_host_key_cannot_attest_to_git_checkout_by_boolean():
    receipt = sign()
    signed_fields = json.loads(receipt.body)
    signed_fields["checkout_clean"] = True
    expect_rejection(resign(signed_fields), "HOST_V2_CHECKOUT_NOT_ATTESTED")


@pytest.mark.parametrize("attr,value,code", [
    ("version", 1, "HOST_V2_TARGET_MISMATCH"),
    ("version", True, "HOST_V2_TARGET_MISMATCH"),
    ("host_id", "different", "HOST_V2_TARGET_MISMATCH"),
    ("repository", "attacker/other", "HOST_V2_TARGET_MISMATCH"),
    ("environment", "prod", "HOST_V2_TARGET_MISMATCH"),
    ("service_id", "gateway", "HOST_V2_TARGET_MISMATCH"),
    ("compose_project", "infra", "HOST_V2_TARGET_MISMATCH"),
    ("container_name", "other-container", "HOST_V2_TARGET_MISMATCH"),
    ("challenge", "b" * 64, "HOST_V2_TARGET_MISMATCH"),
    ("commit_sha", "main", "HOST_V2_IMAGE_INVALID"),
    ("release_image_id", "sha256:" + "f" * 64, "HOST_V2_IMAGE_DRIFT"),
    ("running_image_id", "sha256:" + "f" * 64, "HOST_V2_IMAGE_DRIFT"),
    ("container_id", "container-name", "HOST_V2_IMAGE_INVALID"),
    ("running", "true", "HOST_V2_RECEIPT_INVALID"),
    ("healthy", 1, "HOST_V2_RECEIPT_INVALID"),
    ("checkout_clean", 1, "HOST_V2_RECEIPT_INVALID"),
    ("checkout_clean", True, "HOST_V2_CHECKOUT_NOT_ATTESTED"),
    ("observed_at", "2026-11-16T19:00:00", "HOST_V2_OBSERVATION_INVALID"),
    ("observed_at", "2026-11-16T16:00:00-03:00", "HOST_V2_OBSERVATION_INVALID"),
    ("observed_at", "2026-11-16T18:58:29Z", "HOST_V2_OBSERVATION_STALE"),
    ("observed_at", "2026-11-16T19:00:06Z", "HOST_V2_OBSERVATION_STALE"),
])
def test_validly_mac_authenticated_but_invalid_claims_are_denied(attr, value, code):
    fields = json.loads(sign().body)
    fields[attr] = value
    expect_rejection(resign(fields), code)


def test_even_validly_signed_extra_or_missing_fields_are_not_accepted():
    base = json.loads(sign().body)
    expect_rejection(resign({**base, "can_execute": True}), "HOST_V2_RECEIPT_INVALID")
    removed = dict(base)
    removed.pop("container_name")
    expect_rejection(resign(removed), "HOST_V2_RECEIPT_INVALID")


def test_duplicate_json_keys_and_nan_denied_after_correct_mac():
    receipt = sign()
    raw = receipt.body[:-1] + b',"host_id":"someone-else"}'
    mac = hmac.new(HOST_KEY, _DOMAIN + raw, hashlib.sha256).hexdigest()
    expect_rejection(SignedHostReceipt(raw, mac), "HOST_V2_RECEIPT_INVALID")
    raw = receipt.body[:-1] + b',"random":NaN}'
    mac = hmac.new(HOST_KEY, _DOMAIN + raw, hashlib.sha256).hexdigest()
    expect_rejection(SignedHostReceipt(raw, mac), "HOST_V2_RECEIPT_INVALID")


@pytest.mark.parametrize("secret,expected,now", [
    (b"tiny", CHALLENGE, NOW),
    (HOST_KEY, "not-a-challenge", NOW),
    (HOST_KEY, CHALLENGE, NOW.replace(tzinfo=None)),
    (HOST_KEY, CHALLENGE, "today"),
])
def test_verifier_unconfigured_denies_before_body_read(secret, expected, now):
    expect_rejection(sign(), "HOST_V2_VERIFIER_UNCONFIGURED",
          secret=secret, challenge=expected, now=now)


@pytest.mark.parametrize("invalid", [
    SignedHostReceipt(b"", "a" * 64),
    SignedHostReceipt(b" " * 4000, "a" * 64),
    SignedHostReceipt(b"hello", "not-a-mac"),
])
def test_malformed_oversized_or_invalid_mac_is_denied(invalid):
    expect_rejection(invalid, "HOST_V2_RECEIPT_INVALID")


def test_correctly_signed_stopped_or_unhealthy_container_stays_unready():
    for running, healthy in [(False, True), (True, False), (False, False)]:
        receipt = sign(inspector=Inspect(running=running, healthy=healthy))
        snapshot = verified(receipt)
        assert snapshot.running is running and snapshot.healthy is healthy
        assert not snapshot.rollback_ready and not snapshot.checkout_clean


def test_signer_denies_wrong_image_before_returning_signed_v2_receipt():
    with pytest.raises(HostSigningError, match="RUNNING_IMAGE_NOT_APPROVED"):
        sign(inspector=Inspect(image="sha256:" + "f" * 64))


def test_signer_denies_untrusted_release_record_and_failed_inspector():
    unsigned_record = release_record()
    bad = SignedReleaseRecord(unsigned_record.body, "f" * 64)
    with pytest.raises(HostSigningError, match="RELEASE_RECORD_UNTRUSTED"):
        sign(record=bad)
    with pytest.raises(HostSigningError, match="RUNTIME_INSPECTION_FAILED"):
        sign(inspector=Inspect(fail=True))


def test_host_receipt_v2_is_not_an_executable_or_an_act_permission():
    from pathlib import Path

    source = (
        Path(__file__).resolve().parents[1]
        / "linux_ops_mcp/deploy_host_runtime_v2.py"
    ).read_text()
    assert "docker compose" not in source.lower()
    assert "os.system" not in source
    assert "@router." not in source
    assert "subprocess.run" not in source
    snapshot = verified(sign())
    assert not snapshot.challenge_consumed
    assert snapshot.signature_verified
    assert not snapshot.migrations_safe
    assert not snapshot.rollback_ready
