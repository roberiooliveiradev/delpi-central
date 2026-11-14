"""P3 integration: disposable Postgres only; never touches production Keycloak."""
from __future__ import annotations

import base64
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from tests.test_postgres_integration import database, migrated, pg_client, _sql
from tests.test_postgres_bootstrap_tickets import prepared_machine
from it_portal_app.domain.workstation_device_proof import canonical_challenge, create_challenge
from it_portal_app.domain.workstation_bootstrap_tickets import new_unrouted_ticket
from it_portal_app.infrastructure.persistence.postgres_workstation_bootstrap_tickets import PostgresWorkstationBootstrapTicketStore
from it_portal_app.infrastructure.persistence.postgres_workstation_signed_bootstrap import PostgresSignedBootstrapStore


def pretrusted_key(wid: str):
    private = Ed25519PrivateKey.generate()
    key_id = str(uuid.uuid4())
    public = private.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    _sql(
        "INSERT INTO it_portal.workstation_trusted_device_keys "
        "(id, workstation_id, public_key, state, approved_by_id, approved_at) "
        "VALUES (%s, %s, %s, 'trusted', %s, now()) RETURNING id",
        (key_id, wid, public, "2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11"),
    )
    return key_id, private


def make_signed_case(pg_client):
    wid, actor = prepared_machine(pg_client, "p3")
    ticket, secret = new_unrouted_ticket(wid, ttl_seconds=300)
    PostgresWorkstationBootstrapTicketStore().issue(ticket, actor)
    challenge = create_challenge(ticket.ticket_id, wid, ttl_seconds=180)
    key_id, private = pretrusted_key(wid)
    return wid, actor, ticket, secret, challenge, key_id, private


def signed(private, challenge):
    return base64.urlsafe_b64encode(private.sign(canonical_challenge(challenge))).rstrip(b"=").decode("ascii")


def test_p3_valid_signature_consumes_once_and_never_grants_ingest(pg_client):
    wid, actor, ticket, secret, challenge, key_id, private = make_signed_case(pg_client)
    repo = PostgresSignedBootstrapStore()
    assert repo.bind_pretrusted(challenge, key_id)
    assert not repo.bind_pretrusted(challenge, key_id)
    assert not PostgresWorkstationBootstrapTicketStore().spend(
        ticket_id=ticket.ticket_id, workstation_id=wid, opaque_token=secret
    )
    sig = signed(private, challenge)
    assert not repo.verify_and_spend(challenge, opaque_token="bad", signature=sig)
    assert not repo.verify_and_spend(challenge, opaque_token=secret, signature="bad")
    assert repo.verify_and_spend(challenge, opaque_token=secret, signature=sig)
    assert not repo.verify_and_spend(challenge, opaque_token=secret, signature=sig)
    assert _sql(
        "SELECT ingest_authorized FROM it_portal.workstation_agent_identities WHERE workstation_id = %s",
        (wid,),
    )[0]["ingest_authorized"] is False
    assert _sql(
        "SELECT count(*) AS n FROM it_portal.workstation_bootstrap_ticket_events "
        "WHERE ticket_id = %s AND event_type = 'consumed'", (ticket.ticket_id,),
    )[0]["n"] == 1


def test_p3_unapproved_or_revoked_key_never_binds(pg_client):
    wid, actor, ticket, secret, challenge, key_id, private = make_signed_case(pg_client)
    repo = PostgresSignedBootstrapStore()
    _sql(
        "UPDATE it_portal.workstation_trusted_device_keys SET state = 'revoked', "
        "revoked_at = now() WHERE id = %s RETURNING id", (key_id,)
    )
    assert not repo.bind_pretrusted(challenge, key_id)
    assert not repo.bind_pretrusted(challenge, str(uuid.uuid4()))
    assert not repo.verify_and_spend(challenge, opaque_token=secret, signature=signed(private, challenge))


def test_p3_revoked_after_binding_blocks_existing_signature(pg_client):
    wid, actor, ticket, secret, challenge, key_id, private = make_signed_case(pg_client)
    repo = PostgresSignedBootstrapStore()
    assert repo.bind_pretrusted(challenge, key_id)
    _sql(
        "UPDATE it_portal.workstation_trusted_device_keys SET state = 'revoked', "
        "revoked_at = now() WHERE id = %s RETURNING id", (key_id,)
    )
    assert not repo.verify_and_spend(challenge, opaque_token=secret, signature=signed(private, challenge))
    assert repo_status(ticket.ticket_id, wid) == "pending"


def repo_status(ticket_id, wid):
    return PostgresWorkstationBootstrapTicketStore().status(ticket_id=ticket_id, workstation_id=wid)["state"]


def test_p3_parallel_replay_exactly_one_success(pg_client):
    wid, actor, ticket, secret, challenge, key_id, private = make_signed_case(pg_client)
    repo = PostgresSignedBootstrapStore()
    assert repo.bind_pretrusted(challenge, key_id)
    sig = signed(private, challenge)

    def spend(_):
        return PostgresSignedBootstrapStore().verify_and_spend(
            challenge, opaque_token=secret, signature=sig
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(spend, range(2))) == [False, True]


def test_p3_ticket_cancellation_prevents_signed_spend(pg_client):
    wid, actor, ticket, secret, challenge, key_id, private = make_signed_case(pg_client)
    repo = PostgresSignedBootstrapStore()
    assert repo.bind_pretrusted(challenge, key_id)
    assert PostgresWorkstationBootstrapTicketStore().cancel(
        ticket_id=ticket.ticket_id, workstation_id=wid, actor=actor
    )
    assert not repo.verify_and_spend(challenge, opaque_token=secret, signature=signed(private, challenge))
