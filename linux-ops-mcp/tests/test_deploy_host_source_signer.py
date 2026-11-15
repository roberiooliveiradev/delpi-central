"""Synthetic Docker API and sealed release records, no socket or secrets used."""
from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from linux_ops_mcp.deploy_host_signer import (
    SignedReleaseRecord, HostSigningError, issue_host_receipt,
    verify_release_record, _DOMAIN,
)
from linux_ops_mcp.deploy_host_source import (
    RuntimeTarget, RuntimeContainer, HostSourceError, DockerReadOnlyInspect,
)
from linux_ops_mcp.deploy_host_receipt import verify_host_receipt, HostReceiptError

NOW = datetime(2026, 11, 15, 15, 20, tzinfo=timezone.utc)
TARGET = RuntimeTarget("hml", "it-portal-api", "srv-api-hml", "delpi-hml", "delpi-hml-it-portal-api-1")
EXECUTOR_KEY = b"integration-test-only-release-signing-key-32"
HOST_KEY = b"integration-test-only-host-proof-key-32byte"
SHA = "a" * 40
IMAGE = "sha256:" + "b" * 64
CONTAINER = "c" * 64
CHALLENGE = "f" * 64
RUN_ID = "12345678-1234-4234-8234-1234567890ab"


def record(**updates):
    data = {
        "version": 1, "repository": "roberiooliveiradev/delpi-central",
        "host_id": TARGET.host_id, "environment": TARGET.environment,
        "service_id": TARGET.service_id, "execution_id": RUN_ID,
        "commit_sha": SHA, "image_id": IMAGE,
    }
    data.update(updates)
    body = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    mac = hmac.new(EXECUTOR_KEY, _DOMAIN + body, hashlib.sha256).hexdigest()
    return SignedReleaseRecord(body, mac)


def docker_data(**updates):
    obj = {
        "Id": CONTAINER, "Image": IMAGE,
        "Name": "/" + TARGET.container_name,
        "Config": {"Labels": {
            "com.docker.compose.project": TARGET.compose_project,
            "com.docker.compose.service": TARGET.service_id,
        }, "Env": ["SECRET_SHOULD_NOT_ESCAPE_INSPECT_RESPONSE=hidden"]},
        "State": {"Running": True, "Health": {"Status": "healthy"}},
    }
    obj.update(updates)
    return obj


def inspector(payload=None, *, status=200, events=None):
    def handler(request):
        if events is not None:
            events.append((request.method, request.url.path, request.url.host))
        return httpx.Response(status, json=docker_data() if payload is None else payload)
    return DockerReadOnlyInspect(transport=httpx.MockTransport(handler))


def call(*, source=None, signed=None, target=TARGET, challenge=CHALLENGE,
         release_key=EXECUTOR_KEY, host_key=HOST_KEY, now=NOW):
    return asyncio.run(issue_host_receipt(
        target=target, release_record=record() if signed is None else signed,
        inspector=inspector() if source is None else source,
        release_key=release_key, host_key=host_key, challenge=challenge, now=now,
    ))


def test_end_to_end_receipt_verifies_but_gates_remain_closed():
    calls = []
    receipt = call(source=inspector(events=calls))
    assert calls == [("GET", "/containers/" + TARGET.container_name + "/json", "docker.local")]
    payload = json.loads(receipt.body)
    assert "SECRET_SHOULD_NOT_ESCAPE_INSPECT_RESPONSE" not in repr(payload)
    assert payload["running_image_id"] == IMAGE
    assert payload["checkout_clean"] is False
    proof = verify_host_receipt(
        receipt, secret=HOST_KEY, expected_host_id=TARGET.host_id,
        expected_environment=TARGET.environment, expected_service_id=TARGET.service_id,
        expected_challenge=CHALLENGE, now=NOW,
    )
    assert proof.deployed_commit_sha == SHA
    assert proof.checkout_clean is False
    assert proof.migrations_safe is False and proof.rollback_ready is False


def test_static_target_is_required():
    with pytest.raises(HostSourceError, match="INSPECT_TARGET_INVALID"):
        asyncio.run(inspector().inspect(RuntimeTarget("hml", "../bad", "srv-api-hml", "delpi-hml", "../../etc/passwd")))


@pytest.mark.parametrize("payload,code", [
    (docker_data(Id="not-a-hex"), "INSPECT_IMAGE_INVALID"),
    (docker_data(Image="sha256:" + "A" * 64), "INSPECT_IMAGE_INVALID"),
    (docker_data(Name="/other"), "INSPECT_TARGET_MISMATCH"),
    (docker_data(State={"Running": 1, "Health": {"Status": "healthy"}}), "INSPECT_STATE_INVALID"),
    (docker_data(Config={"Labels": {"com.docker.compose.service": "gateway"}}), "INSPECT_TARGET_MISMATCH"),
])
def test_invalid_docker_inspection_rejected_without_signing(payload, code):
    with pytest.raises(HostSigningError, match="RUNTIME_INSPECTION_FAILED"):
        call(source=inspector(payload))
    with pytest.raises(HostSourceError) as exc:
        asyncio.run(inspector(payload).inspect(TARGET))
    assert exc.value.code == code


@pytest.mark.parametrize("bad", [
    record(service_id="gateway"), record(image_id="sha256:" + "c"*64),
    record(commit_sha="main"), record(repository="other/repo"),
])
def test_forged_or_wrong_release_record_rejected(bad):
    with pytest.raises(HostSigningError):
        call(signed=bad)


def test_wrong_manifest_hmac_cannot_be_reused():
    r = record()
    with pytest.raises(HostSigningError, match="RELEASE_RECORD_UNTRUSTED"):
        call(signed=SignedReleaseRecord(r.body + b" ", r.mac_hex))
    # Domain separation prevents accidentally treating the host key as release key.
    with pytest.raises(HostSigningError, match="SIGNER_NOT_CONFIGURED"):
        call(host_key=EXECUTOR_KEY)


def test_deployed_image_drift_blocks_signing():
    with pytest.raises(HostSigningError, match="RUNNING_IMAGE_NOT_APPROVED"):
        call(source=inspector(docker_data(Image="sha256:" + "a" * 64)))


def test_stop_or_missing_health_never_passes_health_gate():
    for state in ({"Running": False, "Health": {"Status": "healthy"}}, {"Running": True}):
        r = call(source=inspector(docker_data(State=state)))
        p = verify_host_receipt(r, secret=HOST_KEY, expected_host_id=TARGET.host_id,
                                expected_environment="hml", expected_service_id="it-portal-api",
                                expected_challenge=CHALLENGE, now=NOW)
        assert p.service_healthy is False


def test_signature_binds_challenge_and_timestamp():
    r = call()
    for wrong in ["e"*64, "0"*64]:
        with pytest.raises(HostReceiptError, match="HOST_TARGET_MISMATCH"):
            verify_host_receipt(r, secret=HOST_KEY, expected_host_id=TARGET.host_id,
                                expected_environment="hml", expected_service_id="it-portal-api",
                                expected_challenge=wrong, now=NOW)
    with pytest.raises(HostReceiptError, match="HOST_OBSERVATION_STALE"):
        verify_host_receipt(r, secret=HOST_KEY, expected_host_id=TARGET.host_id,
                            expected_environment="hml", expected_service_id="it-portal-api",
                            expected_challenge=CHALLENGE, now=NOW+timedelta(minutes=5))


def test_error_from_untrusted_runtime_cannot_expose_secret():
    class LeakyInspector:
        async def inspect(self, target):
            raise ValueError("DOCKER_ENV=TOP-SECRET")
    with pytest.raises(HostSigningError) as exc:
        call(source=LeakyInspector())
    assert exc.value.code == "RUNTIME_INSPECTION_FAILED" and "TOP-SECRET" not in str(exc.value)


def test_invalid_runtime_dataclass_never_signed():
    class CorruptInspector:
        async def inspect(self, target):
            return RuntimeContainer(CONTAINER, IMAGE, 1, True)
    with pytest.raises(HostSigningError, match="RUNTIME_OBSERVATION_INVALID"):
        call(source=CorruptInspector())
