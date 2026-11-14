"""G2-S4-S2b-P2: offline asymmetric proof; private key lives ONLY in tests."""
from __future__ import annotations

import base64
import uuid
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from it_portal_app.domain.workstation_device_proof import (
    canonical_challenge, create_challenge, verify_pretrusted_device_proof,
)

NOW = datetime(2026, 11, 14, 20, 0, tzinfo=timezone.utc)


def fixture():
    ticket, machine = str(uuid.uuid4()), str(uuid.uuid4())
    challenge = create_challenge(ticket, machine, now=NOW, ttl_seconds=180)
    private = Ed25519PrivateKey.generate()
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    signature = base64.urlsafe_b64encode(private.sign(canonical_challenge(challenge))).rstrip(b"=").decode("ascii")
    return challenge, private, public, signature


def check(c, key, sig, *, ticket=None, machine=None, clock=NOW):
    return verify_pretrusted_device_proof(c, sig, key, ticket_id=ticket or c.ticket_id,
                                          workstation_id=machine or c.workstation_id, now=clock)


def test_correct_pretrusted_key_and_context_pass():
    c, _, public, sig = fixture()
    assert check(c, public, sig)
    assert canonical_challenge(c) == canonical_challenge(c)
    assert b"enrollment-v1" in canonical_challenge(c)


def test_wrong_key_or_tampering_fails():
    c, _, public, sig = fixture()
    attacker = Ed25519PrivateKey.generate().public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    assert not check(c, attacker, sig)
    assert not check(replace(c, workstation_id=str(uuid.uuid4())), public, sig)
    assert not check(replace(c, ticket_id=str(uuid.uuid4())), public, sig)
    assert not check(replace(c, nonce="A" * 43), public, sig)
    assert not check(replace(c, audience="other-app"), public, sig)
    assert not check(c, public, sig, ticket=str(uuid.uuid4()))
    assert not check(c, public, sig, machine=str(uuid.uuid4()))


def test_timing_fails_closed():
    c, _, public, sig = fixture()
    assert check(c, public, sig, clock=NOW + timedelta(seconds=179))
    assert not check(c, public, sig, clock=NOW + timedelta(seconds=180))
    assert not check(c, public, sig, clock=NOW - timedelta(seconds=31))
    assert not check(replace(c, expires_at=c.issued_at + timedelta(hours=1)), public, sig)
    assert not check(replace(c, issued_at=NOW + timedelta(seconds=1)), public, sig)


@pytest.mark.parametrize("bad", ["", "x", "abc!", "A" * 86, "A" * 87, None, 3])
def test_malformed_signature_rejected(bad):
    c, _, public, _ = fixture()
    assert not check(c, public, bad)


@pytest.mark.parametrize("ttl", [0, 59, 601, None, True, 90.5])
def test_invalid_lifetime_rejected(ttl):
    with pytest.raises(ValueError):
        create_challenge(str(uuid.uuid4()), str(uuid.uuid4()), now=NOW, ttl_seconds=ttl)


def test_cryptographic_key_not_a_device_identity_by_itself():
    c, _, key, sig = fixture()
    assert check(c, key, sig)
    assert not check(c, b"\\x00", sig)


def test_no_private_key_in_production_module():
    from pathlib import Path
    import it_portal_app.domain.workstation_device_proof as module
    code = Path(module.__file__).read_text(encoding="utf-8")
    assert "Ed25519PrivateKey" not in code
    assert "@router" not in code
    assert "ingest_authorized" not in code


def test_challenge_factory_normalizes_microseconds_for_real_runtime():
    instant = NOW.replace(microsecond=567890)
    ticket, machine = str(uuid.uuid4()), str(uuid.uuid4())
    challenge = create_challenge(ticket, machine, now=instant, ttl_seconds=180)
    assert challenge.issued_at.microsecond == 0
    assert challenge.expires_at.microsecond == 0
    canonical_challenge(challenge)
    private = Ed25519PrivateKey.generate()
    pub = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    signed = base64.urlsafe_b64encode(private.sign(canonical_challenge(challenge))).rstrip(b"=").decode()
    assert verify_pretrusted_device_proof(
        challenge, signed, pub, ticket_id=ticket, workstation_id=machine,
        now=instant + timedelta(seconds=1)
    )
