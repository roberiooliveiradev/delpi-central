"""Ed25519 trust tests; keys generated in-process, never from Git."""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_snapshot_trust import (
    HMLSnapshotTrustError,
    build_keyring,
    generate_fixture_keypair,
    sign_snapshot_envelope,
    verify_signed_snapshot_envelope,
)

_NOW = datetime(2026, 11, 17, 20, 5, tzinfo=timezone.utc)
_PAYLOAD = json.dumps({
    "schema": "atlas.hml.inspect.v1",
    "source": "root-one-shot-snapshot-claim-untrusted",
    "environment": "hml",
    "compose_project": "delpi-hml",
    "service_id": "public-hub",
    "container_name": "delpi-hml-public-hub",
    "container_id": "a" * 64,
    "image_id": "sha256:" + "b" * 64,
    "running": True,
    "healthy": True,
    "observed_at": "2026-11-17T20:05:00Z",
}, separators=(",", ":"), sort_keys=True).encode("ascii")


@pytest.fixture
def keys():
    private, public, key_id = generate_fixture_keypair()
    ring = build_keyring(active=((key_id, public),))
    return private, public, key_id, ring


def test_sign_and_verify_succeeds_but_not_independent(keys):
    private, public, key_id, ring = keys
    sealed = sign_snapshot_envelope(
        _PAYLOAD, generation=1, produced_at=_NOW,
        private_key=private, public_key=public,
    )
    review = verify_signed_snapshot_envelope(sealed, now=_NOW, keyring=ring)
    assert review.signature_verified
    assert review.status == "blocked"
    assert not review.authenticity_independent
    assert not review.prepare_eligible and not review.can_execute
    assert review.envelope.key_id == key_id
    assert "ROOT_WITH_PRIVATE_KEY_ACCESS_CAN_FORGE" in review.blocks


def test_tampered_payload_fails_signature(keys):
    private, public, _, ring = keys
    sealed = bytearray(sign_snapshot_envelope(
        _PAYLOAD, generation=1, produced_at=_NOW,
        private_key=private, public_key=public,
    ))
    # Flip one byte inside the JSON without breaking UTF-8 structure hard.
    idx = sealed.find(b"healthy")
    sealed[idx] ^= 0x01
    with pytest.raises(HMLSnapshotTrustError) as err:
        verify_signed_snapshot_envelope(bytes(sealed), now=_NOW, keyring=ring)
    assert err.value.code in {
        "HML_TRUST_SIGNATURE_INVALID",
        "HML_ENVELOPE_JSON_INVALID",
        "HML_ENVELOPE_DIGEST_MISMATCH",
        "HML_ENVELOPE_FIELD_INVALID",
    }


def test_revoked_key_is_rejected(keys):
    private, public, key_id, _ = keys
    sealed = sign_snapshot_envelope(
        _PAYLOAD, generation=2, produced_at=_NOW,
        private_key=private, public_key=public,
    )
    old_private, old_public, old_id = generate_fixture_keypair()
    ring = build_keyring(
        active=((old_id, old_public),),
        revoked=((key_id, public),),
    )
    with pytest.raises(HMLSnapshotTrustError) as err:
        verify_signed_snapshot_envelope(sealed, now=_NOW, keyring=ring)
    assert err.value.code == "HML_TRUST_KEY_REVOKED"
    # Rotation: new key signs and verifies.
    rotated = sign_snapshot_envelope(
        _PAYLOAD, generation=3, produced_at=_NOW,
        private_key=old_private, public_key=old_public,
    )
    ok = verify_signed_snapshot_envelope(rotated, now=_NOW, keyring=ring)
    assert ok.signature_verified and not ok.can_execute


def test_unknown_key_id_denied(keys):
    private, public, _, _ = keys
    sealed = sign_snapshot_envelope(
        _PAYLOAD, generation=1, produced_at=_NOW,
        private_key=private, public_key=public,
    )
    other_private, other_public, other_id = generate_fixture_keypair()
    ring = build_keyring(active=((other_id, other_public),))
    with pytest.raises(HMLSnapshotTrustError) as err:
        verify_signed_snapshot_envelope(sealed, now=_NOW, keyring=ring)
    assert err.value.code == "HML_TRUST_KEY_UNKNOWN"
    del other_private  # ensure fixture private is not persisted
