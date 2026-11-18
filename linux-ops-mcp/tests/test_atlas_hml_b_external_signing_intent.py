"""Pure signer-intent and disposable subprocess key-custody exercises.

A separate CI child holds a generated private key; the requesting test process
receives only a public key + signature. This is NOT an independent trust domain
against root on the real Linux host, and makes no Docker or network calls.
"""
from __future__ import annotations

import base64
import inspect
import os
import subprocess
import sys
from dataclasses import replace
from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from linux_ops_mcp.atlas_hml_b_external_signing_intent import (
    HMLExternalSigningError,
    prepare_signing_intent,
    review_signing_intent_for_external_signer,
    seal_externally_signed_intent,
)
from linux_ops_mcp.atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError, build_keyring,
    generate_fixture_keypair, key_id_for_public_key,
)
from linux_ops_mcp.deploy_host_source import RuntimeContainer

NOW = datetime(2026, 11, 17, 23, 0, tzinfo=timezone.utc)
HML = RuntimeContainer(
    container_id="a" * 64, image_id="sha256:" + "b" * 64,
    running=True, healthy=True,
)


@pytest.fixture
def sample():
    private, public, key_id = generate_fixture_keypair()
    intent = prepare_signing_intent(
        HML, observed_at=NOW, generation=1, key_id=key_id,
    )
    ring = build_keyring(active=((key_id, public),))
    return private, public, intent, ring


def denied(code, fn):
    with pytest.raises(HMLExternalSigningError) as err:
        fn()
    assert err.value.code == code


def test_keyless_request_policy_and_sealing_remain_blocked(sample):
    private, public, intent, ring = sample
    assert "private_key" not in inspect.signature(prepare_signing_intent).parameters
    assert "private_key" not in inspect.signature(seal_externally_signed_intent).parameters
    checked = review_signing_intent_for_external_signer(
        intent, now=NOW, expected_generation=1,
    )
    assert checked.status == "blocked"
    assert not checked.producer_isolation_attested
    signature = Ed25519PrivateKey.from_private_bytes(private).sign(intent.signing_bytes)
    result = seal_externally_signed_intent(
        intent, signature=signature, keyring=ring, now=NOW,
    )
    assert result.signature_verified and result.status == "blocked"
    assert not result.signer_independently_attested
    assert not result.key_custody_independent
    assert not result.can_execute and not result.prepare_eligible
    assert b"private" not in result.envelope


@pytest.mark.parametrize("mutator,reason", [
    (lambda x: replace(x, generation=2), "HML_SIGNING_INTENT_COUNTER_DENIED"),
    (lambda x: replace(x, signing_bytes=b"fake"), "HML_SIGNING_INTENT_SCOPE_DENIED"),
    (lambda x: replace(x, payload=b'{"environment":"prod"}'), "HML_SIGNING_INTENT_SCOPE_DENIED"),
    (lambda x: replace(x, can_execute=True), "HML_SIGNING_INTENT_POLICY_INVALID"),
    (lambda x: replace(x, key_custody_independent=True), "HML_SIGNING_INTENT_POLICY_INVALID"),
    (lambda x: replace(x, produced_at=NOW.replace(tzinfo=None)),
     "HML_SIGNING_INTENT_POLICY_INVALID"),
])
def test_forged_or_wrong_scope_signing_request_denied(sample, mutator, reason):
    _, _, intent, _ = sample
    denied(reason, lambda: review_signing_intent_for_external_signer(
        mutator(intent), now=NOW, expected_generation=1,
    ))


def test_wrong_signature_and_revoked_key_fail_closed(sample):
    private, public, intent, ring = sample
    denied("HML_SIGNING_SIGNATURE_INVALID", lambda: seal_externally_signed_intent(
        intent, signature=b"\x00" * 64, keyring=ring, now=NOW,
    ))
    key_id = key_id_for_public_key(public)
    other_private, other_pub, other_id = generate_fixture_keypair()
    revoked = build_keyring(
        active=((other_id, other_pub),),
        revoked=((key_id, public),),
    )
    signature = Ed25519PrivateKey.from_private_bytes(private).sign(intent.signing_bytes)
    denied("HML_SIGNING_SIGNATURE_INVALID", lambda: seal_externally_signed_intent(
        intent, signature=signature, keyring=revoked, now=NOW,
    ))
    del other_private


def test_keyring_refuses_identity_not_derived_from_public_key(sample):
    _, public, _, _ = sample
    with pytest.raises(HMLSnapshotTrustError) as err:
        build_keyring(active=(("f" * 32, public),))
    assert err.value.code == "HML_TRUST_KEYRING_INVALID"


def test_forged_keyring_object_refuses_wrong_public_binding(sample):
    from linux_ops_mcp.atlas_hml_b_snapshot_trust import HMLTrustKeyring, HMLPublicKeyRecord
    _, public, intent, _ = sample
    wrong_ring = HMLTrustKeyring(
        keys=(HMLPublicKeyRecord(key_id=intent.key_id, public_key=b"\x01" * 32),),
    )
    with pytest.raises(HMLSnapshotTrustError):
        wrong_ring.active_public(intent.key_id)


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="Linux ephemeral process fixture")
def test_signature_produced_in_disposable_child_only():
    """Private signing key is GENERATED within the temporary child process.

    Neither the producer-oriented intent nor the parent receives that key.
    The test does not grant a real independent root-resistant key boundary.
    """
    script = r"""
import base64
import sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

key = Ed25519PrivateKey.generate()
public = key.public_key().public_bytes_raw()
sys.stdout.write(base64.b64encode(public).decode("ascii") + "\n")
sys.stdout.flush()
message = base64.b64decode(sys.stdin.buffer.readline().strip(), validate=True)
signature = key.sign(message)
sys.stdout.write(base64.b64encode(signature).decode("ascii") + "\n")
sys.stdout.flush()
"""
    child = subprocess.Popen(
        [sys.executable, "-B", "-c", script],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PYTHONDONTWRITEBYTECODE": "1"},
    )
    try:
        assert child.stdout is not None and child.stdin is not None
        public = base64.b64decode(child.stdout.readline().strip(), validate=True)
        intent = prepare_signing_intent(
            HML, observed_at=NOW, generation=1,
            key_id=key_id_for_public_key(public),
        )
        review_signing_intent_for_external_signer(
            intent, now=NOW, expected_generation=1,
        )
        child.stdin.write(base64.b64encode(intent.signing_bytes) + b"\n")
        child.stdin.flush()
        child.stdin.close()
        signature = base64.b64decode(child.stdout.readline().strip(), validate=True)
        assert child.wait(timeout=8) == 0
        ring = build_keyring(active=((intent.key_id, public),))
        reviewed = seal_externally_signed_intent(
            intent, signature=signature, now=NOW, keyring=ring,
        )
        assert reviewed.signature_verified
        assert not reviewed.key_custody_independent
        assert not reviewed.producer_isolation_attested
        assert not reviewed.can_execute and not reviewed.prepare_eligible
    finally:
        if child.poll() is None:
            child.kill()
            child.wait(timeout=3)
