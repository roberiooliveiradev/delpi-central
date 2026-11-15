"""P2.2c: offline negative tests for a signed runtime release receipt."""
from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.deploy_host_receipt import HostReceiptError, SignedHostReceipt, verify_host_receipt

NOW = datetime(2026, 11, 15, 13, 30, tzinfo=timezone.utc)
SECRET = b"local-test-only-key-32-bytes-not-production"  # fixture, not a credential
HOST = "srv-api-pilot"
CHALLENGE = "e" * 64
IMAGE = "sha256:" + "c" * 64


def payload(**changes):
    data = {
        "version": 1,
        "host_id": HOST, "repository": "roberiooliveiradev/delpi-central",
        "environment": "hml", "service_id": "it-portal-api",
        "commit_sha": "a" * 40, "release_image_id": IMAGE,
        "running_image_id": IMAGE, "container_id": "d" * 64,
        "running": True, "healthy": True, "checkout_clean": True,
        "observed_at": NOW.isoformat().replace("+00:00", "Z"),
        "challenge": CHALLENGE,
    }
    data.update(changes)
    return data


def signed(data):
    body = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    mac = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    return SignedHostReceipt(body, mac)


def verify(receipt, **changes):
    kw = dict(secret=SECRET, expected_host_id=HOST, expected_environment="hml",
              expected_service_id="it-portal-api", expected_challenge=CHALLENGE, now=NOW)
    kw.update(changes)
    return verify_host_receipt(receipt, **kw)


def test_valid_receipt_binds_live_image_but_does_not_approve_migration_or_rollback():
    proof = verify(signed(payload()))
    assert proof.deployed_commit_sha == "a" * 40
    assert proof.service_healthy is True and proof.checkout_clean is True
    assert proof.migrations_safe is False and proof.rollback_ready is False
    assert proof.checked_at == NOW


def test_valid_signed_stopped_container_stays_unhealthy():
    proof = verify(signed(payload(running=False, healthy=True, checkout_clean=False)))
    assert proof.service_healthy is False and proof.checkout_clean is False


def test_signature_tamper_and_wrong_secret_are_rejected():
    receipt = signed(payload())
    bad = SignedHostReceipt(receipt.body + b" ", receipt.mac_hex)
    with pytest.raises(HostReceiptError, match="HOST_SIGNATURE_INVALID"):
        verify(bad)
    with pytest.raises(HostReceiptError, match="HOST_SIGNATURE_INVALID"):
        verify(receipt, secret=b"different-secret-material-thirty-two-bytes")


@pytest.mark.parametrize("field,value,code", [
    ("version", True, "HOST_TARGET_MISMATCH"),
    ("host_id", "other-host", "HOST_TARGET_MISMATCH"),
    ("repository", "attacker/repo", "HOST_TARGET_MISMATCH"),
    ("environment", "prod", "HOST_TARGET_MISMATCH"),
    ("service_id", "gateway", "HOST_TARGET_MISMATCH"),
    ("challenge", "f" * 64, "HOST_TARGET_MISMATCH"),
    ("commit_sha", "main", "HOST_RELEASE_ID_INVALID"),
    ("commit_sha", "A" * 40, "HOST_RELEASE_ID_INVALID"),
    ("release_image_id", "sha256:" + "1" * 64, "HOST_IMAGE_DRIFT"),
    ("running_image_id", "sha256:" + "1" * 64, "HOST_IMAGE_DRIFT"),
    ("container_id", "container-name", "HOST_RELEASE_ID_INVALID"),
    ("running", 1, "HOST_RECEIPT_INVALID"),
    ("healthy", "true", "HOST_RECEIPT_INVALID"),
    ("checkout_clean", 1, "HOST_RECEIPT_INVALID"),
    ("observed_at", "2026-11-15T13:30:00", "HOST_OBSERVATION_TIME_INVALID"),
    ("observed_at", "2026-11-15T13:30:00+03:00", "HOST_OBSERVATION_TIME_INVALID"),
    ("observed_at", (NOW - timedelta(seconds=91)).isoformat().replace("+00:00", "Z"), "HOST_OBSERVATION_STALE"),
    ("observed_at", (NOW + timedelta(seconds=6)).isoformat().replace("+00:00", "Z"), "HOST_OBSERVATION_STALE"),
])
def test_signed_but_invalid_observations_fail_closed(field, value, code):
    with pytest.raises(HostReceiptError) as exc:
        verify(signed(payload(**{field: value})))
    assert exc.value.code == code


def test_unknown_and_missing_fields_rejected_even_when_signed():
    data = payload(command="rm -rf /")
    with pytest.raises(HostReceiptError, match="HOST_RECEIPT_INVALID"):
        verify(signed(data))
    data = payload()
    del data["challenge"]
    with pytest.raises(HostReceiptError, match="HOST_RECEIPT_INVALID"):
        verify(signed(data))


def test_duplicate_json_fields_rejected_even_with_correct_mac():
    body = signed(payload()).body
    body = body[:-1] + b',"host_id":"other"}'
    mac = hmac.new(SECRET, body, hashlib.sha256).hexdigest()
    with pytest.raises(HostReceiptError, match="HOST_RECEIPT_INVALID"):
        verify(SignedHostReceipt(body, mac))


@pytest.mark.parametrize("kwargs", [
    {"secret": b"short"}, {"expected_host_id": ""},
    {"expected_environment": "dev"},
    {"expected_service_id": "it-portal-api;sudo"},
    {"expected_challenge": "bad"},
    {"now": NOW.replace(tzinfo=None)},
])
def test_unconfigured_verifier_never_accepts_receipts(kwargs):
    with pytest.raises(HostReceiptError, match="HOST_VERIFIER_UNCONFIGURED"):
        verify(signed(payload()), **kwargs)


def test_too_large_body_and_signature_with_wrong_type_fail():
    valid = signed(payload())
    with pytest.raises(HostReceiptError, match="HOST_RECEIPT_INVALID"):
        verify(SignedHostReceipt(valid.body + b" " * 2200, valid.mac_hex))
    with pytest.raises(HostReceiptError, match="HOST_RECEIPT_INVALID"):
        verify(SignedHostReceipt(valid.body, "not-hex"))
