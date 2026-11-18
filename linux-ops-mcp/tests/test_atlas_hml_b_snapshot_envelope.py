"""Envelope shape/digest tests; no Docker, no host writes."""
from __future__ import annotations

import base64
import hashlib
import json
from datetime import datetime, timedelta, timezone

import pytest

from linux_ops_mcp.atlas_hml_b_snapshot_envelope import (
    HMLSnapshotEnvelopeError,
    build_unsigned_envelope_document,
    review_snapshot_envelope,
    seal_envelope_document,
    signing_message,
)

_NOW = datetime(2026, 11, 17, 20, 0, tzinfo=timezone.utc)
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
    "observed_at": "2026-11-17T20:00:00Z",
}, separators=(",", ":"), sort_keys=True).encode("ascii")


def _envelope(**changes):
    doc = build_unsigned_envelope_document(
        _PAYLOAD, generation=1, produced_at=_NOW, key_id="ab" * 16,
    )
    doc.update(changes)
    if "signature_b64" not in changes:
        doc["signature_b64"] = base64.b64encode(b"\x01" * 64).decode("ascii")
    return json.dumps(doc, separators=(",", ":"), sort_keys=True).encode("ascii")


def test_review_accepts_well_formed_envelope_but_stays_blocked():
    review = review_snapshot_envelope(_envelope(), now=_NOW)
    assert review.status == "blocked"
    assert review.generation == 1
    assert review.diagnostic.status == "blocked"
    assert not review.authenticity_independent
    assert not review.prepare_eligible and not review.can_execute
    assert "LEGACY_BARE_JSON_NOT_AUTHENTICATED" in review.blocks
    assert len(review.signature) == 64
    assert review.signed_message.startswith(b"atlas.hml.snapshot-envelope.v1\x00")


def test_legacy_bare_json_is_not_silently_authenticated():
    with pytest.raises(HMLSnapshotEnvelopeError) as err:
        review_snapshot_envelope(_PAYLOAD, now=_NOW)
    assert err.value.code == "HML_ENVELOPE_SCHEMA_INVALID"


def test_prod_target_denied():
    with pytest.raises(HMLSnapshotEnvelopeError) as err:
        review_snapshot_envelope(_envelope(environment="prod"), now=_NOW)
    assert err.value.code == "HML_ENVELOPE_TARGET_DENIED"


def test_digest_mismatch_denied():
    with pytest.raises(HMLSnapshotEnvelopeError) as err:
        review_snapshot_envelope(
            _envelope(payload_sha256="0" * 64), now=_NOW,
        )
    assert err.value.code == "HML_ENVELOPE_DIGEST_MISMATCH"


def test_truncated_or_future_inner_payload_denied():
    stale = dict(json.loads(_PAYLOAD.decode()))
    stale["observed_at"] = "2026-11-17T18:00:00Z"
    payload = json.dumps(stale, separators=(",", ":"), sort_keys=True).encode()
    doc = build_unsigned_envelope_document(
        payload, generation=1, produced_at=_NOW, key_id="cd" * 16,
    )
    raw = seal_envelope_document(doc, signature=b"\x02" * 64)
    with pytest.raises(HMLSnapshotEnvelopeError) as err:
        review_snapshot_envelope(raw, now=_NOW)
    assert err.value.code == "HML_SNAPSHOT_EXPIRED_OR_FUTURE"


def test_signing_message_is_domain_separated_and_stable():
    digest = hashlib.sha256(_PAYLOAD).hexdigest()
    first = signing_message(
        generation=3, produced_at="2026-11-17T20:00:00Z",
        payload_sha256=digest, key_id="ef" * 16, payload=_PAYLOAD,
    )
    second = signing_message(
        generation=3, produced_at="2026-11-17T20:00:00Z",
        payload_sha256=digest, key_id="ef" * 16, payload=_PAYLOAD,
    )
    assert first == second and b"\x00" in first
