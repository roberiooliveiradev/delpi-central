"""G2-S4-S2b-P1: pure, isolated ticket tests with no network/DB access."""
from __future__ import annotations

import uuid

import pytest

from it_portal_app.domain.workstation_bootstrap_tickets import (
    DEFAULT_TTL_SECONDS, matches_ticket, new_unrouted_ticket, ticket_digest,
)


def test_ticket_is_random_scoped_and_redacted():
    wid = str(uuid.uuid4())
    first, raw = new_unrouted_ticket(wid)
    other, other_raw = new_unrouted_ticket(wid)
    assert first.workstation_id == wid
    assert first.ttl_seconds == DEFAULT_TTL_SECONDS
    assert first.ticket_id != other.ticket_id
    assert raw != other_raw
    assert first.token_digest != other.token_digest
    assert len(raw) == 43
    assert raw not in repr(first)
    assert raw not in str(first)
    from dataclasses import asdict
    assert raw not in str(asdict(first))
    assert len(first.token_digest) == 64
    assert matches_ticket(raw, first.token_digest)
    assert not matches_ticket(other_raw, first.token_digest)


@pytest.mark.parametrize("ttl", [0, 59, 601, 100000, -4, 2.5, True, None, "300"])
def test_ttl_must_be_short_and_exact_int(ttl):
    with pytest.raises(ValueError, match="duracao"):
        new_unrouted_ticket(str(uuid.uuid4()), ttl_seconds=ttl)


@pytest.mark.parametrize("wid", [None, "", "xyz", str(uuid.UUID(int=0)), "ABC", 42])
def test_noncanonical_or_empty_device_identity_rejected(wid):
    with pytest.raises(ValueError, match="workstation_id"):
        new_unrouted_ticket(wid)


def test_token_fingerprint_rejects_malformed_without_leaking_secret():
    _, token = new_unrouted_ticket(str(uuid.uuid4()))
    with pytest.raises(ValueError, match="ticket invalido") as err:
        ticket_digest(token + "\nsecret")
    assert token not in str(err.value)
    assert not matches_ticket(token + "\n", ticket_digest(token))
    assert not matches_ticket(token, "x" * 64)
    assert not matches_ticket(token, None)
    assert not matches_ticket(42, ticket_digest(token))


def test_ticket_metadata_never_contains_secret():
    first, raw = new_unrouted_ticket(str(uuid.uuid4()))
    from dataclasses import replace
    assert first == replace(first, token_digest=first.token_digest)
    assert raw not in repr(first)


def test_legal_ttl_bounds():
    wid = str(uuid.uuid4())
    assert new_unrouted_ticket(wid, ttl_seconds=60)[0].ttl_seconds == 60
    assert new_unrouted_ticket(wid, ttl_seconds=600)[0].ttl_seconds == 600
