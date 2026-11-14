"""PostgreSQL 16 disposable integration: inert, one-time enrollment tickets (V014)."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.test_postgres_integration import pg_client, _sql
from it_portal_app.application.ports import Actor
from it_portal_app.application.workstation_identity_service import device_client_id
from it_portal_app.domain.errors import ConflictError
from it_portal_app.domain.workstation_bootstrap_tickets import new_unrouted_ticket
from it_portal_app.infrastructure.persistence.postgres_workstation_identities import (
    PostgresWorkstationIdentityStore,
)
from it_portal_app.infrastructure.persistence.postgres_workstation_bootstrap_tickets import (
    PostgresWorkstationBootstrapTicketStore,
)

pytestmark = pytest.mark.skipif(not os.getenv("IT_PORTAL_TEST_DSN"), reason="Postgres descartavel nao configurado")


def prepared_machine(pg_client, label: str):
    machine = pg_client.post("/workstations", json={
        "name": "Piloto ticket sem agente",
        "hostname": f"g2s4b-{label}-{uuid.uuid4().hex[:7]}",
        "unit_code": "02", "device_kind": "desktop",
        "administrative_status": "in_operation",
    })
    assert machine.status_code == 201, machine.text
    wid = machine.json()["data"]["id"]
    actor = Actor(id="2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11", name="Ana TI")
    identity = PostgresWorkstationIdentityStore()
    identity.reserve(wid, device_client_id(wid), actor)
    identity.prepared(wid, str(uuid.uuid4()), actor)
    return wid, actor


def test_v014_ticket_issue_and_exactly_once(pg_client):
    wid, actor = prepared_machine(pg_client, "one")
    store = PostgresWorkstationBootstrapTicketStore()
    ticket, secret = new_unrouted_ticket(wid)
    issued = store.issue(ticket, actor)
    assert issued["state"] == "pending"
    assert "opaque_token" not in issued and "token_digest" not in issued
    with pytest.raises(ConflictError):
        store.issue(new_unrouted_ticket(wid)[0], actor)
    stored = _sql("SELECT token_digest FROM it_portal.workstation_bootstrap_tickets WHERE id = %s", (ticket.ticket_id,))[0]
    assert stored["token_digest"].strip() == ticket.token_digest
    assert secret != stored["token_digest"].strip()
    assert not store.spend(ticket_id=ticket.ticket_id, workstation_id=str(uuid.uuid4()), opaque_token=secret)
    assert not store.spend(ticket_id=ticket.ticket_id, workstation_id=wid, opaque_token="invalid")
    assert store.spend(ticket_id=ticket.ticket_id, workstation_id=wid, opaque_token=secret)
    assert not store.spend(ticket_id=ticket.ticket_id, workstation_id=wid, opaque_token=secret)
    assert store.status(ticket_id=ticket.ticket_id, workstation_id=wid)["state"] == "consumed"
    row = _sql("SELECT ingest_authorized, state FROM it_portal.workstation_agent_identities WHERE workstation_id = %s", (wid,))[0]
    assert row == {"ingest_authorized": False, "state": "prepared"}
    assert _sql("SELECT COUNT(*) AS n FROM it_portal.workstation_bootstrap_ticket_events WHERE ticket_id = %s AND event_type = 'consumed'", (ticket.ticket_id,))[0]["n"] == 1


def test_v014_ticket_expiration_and_cancel(pg_client):
    wid, actor = prepared_machine(pg_client, "expiry")
    store = PostgresWorkstationBootstrapTicketStore()
    previous, old_secret = new_unrouted_ticket(wid, ttl_seconds=60)
    store.issue(previous, actor)
    _sql(
        "UPDATE it_portal.workstation_bootstrap_tickets "
        "SET issued_at = issued_at - INTERVAL '5 minutes', "
        "expires_at = expires_at - INTERVAL '5 minutes' WHERE id = %s",
        (previous.ticket_id,),
    )
    assert not store.spend(ticket_id=previous.ticket_id, workstation_id=wid, opaque_token=old_secret)
    replacement, next_secret = new_unrouted_ticket(wid)
    store.issue(replacement, actor)
    assert store.status(ticket_id=previous.ticket_id, workstation_id=wid)["state"] == "expired"
    assert store.cancel(ticket_id=replacement.ticket_id, workstation_id=wid, actor=actor)
    assert not store.cancel(ticket_id=replacement.ticket_id, workstation_id=wid, actor=actor)
    assert not store.spend(ticket_id=replacement.ticket_id, workstation_id=wid, opaque_token=next_secret)
    assert store.status(ticket_id=replacement.ticket_id, workstation_id=wid)["state"] == "cancelled"


def test_v014_ticket_two_concurrent_attempts_only_one_succeeds(pg_client):
    wid, actor = prepared_machine(pg_client, "race")
    ticket, secret = new_unrouted_ticket(wid)
    PostgresWorkstationBootstrapTicketStore().issue(ticket, actor)
    def attempt(_):
        return PostgresWorkstationBootstrapTicketStore().spend(
            ticket_id=ticket.ticket_id, workstation_id=wid, opaque_token=secret
        )
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(attempt, range(2)))
    assert sorted(results) == [False, True]


def test_v014_no_ticket_without_prepared_identity(pg_client):
    machine = pg_client.post("/workstations", json={
        "name": "Sem identidade preparada", "hostname": "g2s4b-no-id-" + uuid.uuid4().hex[:8],
        "unit_code": "02", "device_kind": "desktop",
        "administrative_status": "in_operation",
    })
    assert machine.status_code == 201, machine.text
    actor = Actor(id="2b0c7a52-6f7e-4d3c-9a51-0f4f1c2d9e11", name="Ana TI")
    with pytest.raises(ConflictError):
        PostgresWorkstationBootstrapTicketStore().issue(
            new_unrouted_ticket(machine.json()["data"]["id"])[0], actor
        )
