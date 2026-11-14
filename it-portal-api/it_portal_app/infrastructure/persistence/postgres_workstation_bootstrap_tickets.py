"""Unrouted G2-S4-S2b-P1 ticket ledger, isolated from activation and HTTP.

Possession of an opaque token is NOT Windows device attestation. This store
never changes ingest_authorized, Keycloak clients, Windows agents or RBAC.
"""
from __future__ import annotations

import uuid

from it_portal_app.application.ports import Actor
from it_portal_app.domain.errors import ConflictError, NotFoundError
from it_portal_app.domain.workstation_bootstrap_tickets import (
    UnroutedTicket, ticket_digest,
)
from it_portal_app.infrastructure.persistence.postgres_base import PostgresRepositoryBase

TICKETS = "it_portal.workstation_bootstrap_tickets"
EVENTS = "it_portal.workstation_bootstrap_ticket_events"


class PostgresWorkstationBootstrapTicketStore(PostgresRepositoryBase):
    @staticmethod
    def _event(conn, ticket_id: str, event_type: str, actor_id: str | None) -> None:
        conn.execute(
            f"INSERT INTO {EVENTS} (id, ticket_id, event_type, actor_id) VALUES (%s, %s, %s, %s)",
            (str(uuid.uuid4()), ticket_id, event_type, actor_id),
        )

    def issue(self, ticket: UnroutedTicket, actor: Actor) -> dict:
        """Reserves hash only; caller must keep secret off browser, logs and DB."""
        with self._tx() as conn:
            machine = conn.execute(
                "SELECT archived_at, administrative_status "
                "FROM it_portal.workstations WHERE id = %s FOR UPDATE",
                (ticket.workstation_id,),
            ).fetchone()
            if machine is None:
                raise NotFoundError("workstation_not_found", "Computador nao encontrado.")
            if machine["archived_at"] is not None or machine["administrative_status"] != "in_operation":
                raise ConflictError("workstation_not_eligible", "Computador indisponivel para convite.")
            identity = conn.execute(
                "SELECT state, revocation_status, ingest_authorized "
                "FROM it_portal.workstation_agent_identities WHERE workstation_id = %s FOR SHARE",
                (ticket.workstation_id,),
            ).fetchone()
            if (identity is None or identity["state"] != "prepared"
                    or identity["revocation_status"] != "none"
                    or identity["ingest_authorized"] is not False):
                raise ConflictError(
                    "workstation_identity_not_eligible", "Identidade nao preparada ou nao segura."
                )
            stale = conn.execute(
                f"UPDATE {TICKETS} SET state = 'expired', closed_at = now() "
                "WHERE workstation_id = %s AND state = 'pending' AND expires_at <= now() "
                "RETURNING id",
                (ticket.workstation_id,),
            ).fetchall()
            for row in stale:
                self._event(conn, str(row["id"]), "expired", None)
            active = conn.execute(
                f"SELECT id FROM {TICKETS} WHERE workstation_id = %s AND state = 'pending'",
                (ticket.workstation_id,),
            ).fetchone()
            if active is not None:
                raise ConflictError("workstation_bootstrap_pending", "Convite ativo requer cancelamento ou expiracao.")
            row = conn.execute(
                f"INSERT INTO {TICKETS} "
                "(id, workstation_id, token_digest, issued_by_id, expires_at) "
                "VALUES (%s, %s, %s, %s, now() + (%s * INTERVAL '1 second')) "
                "RETURNING id, workstation_id, issued_at, expires_at, state",
                (ticket.ticket_id, ticket.workstation_id, ticket.token_digest,
                 actor.id, ticket.ttl_seconds),
            ).fetchone()
            self._event(conn, ticket.ticket_id, "issued", actor.id)
            return dict(row)  # Never expose token_digest or opaque_token.

    def spend(self, *, ticket_id: str, workstation_id: str, opaque_token: str) -> bool:
        """Atomic one-time proof of bearer possession, NOT a device authorization."""
        try:
            digest = ticket_digest(opaque_token)
        except ValueError:
            return False
        with self._tx() as conn:
            row = conn.execute(
                f"UPDATE {TICKETS} AS ticket "
                "SET state = 'consumed', closed_at = now() "
                "FROM it_portal.workstations AS station, "
                "it_portal.workstation_agent_identities AS identity "
                "WHERE ticket.id = %s AND ticket.workstation_id = %s "
                "AND ticket.token_digest = %s AND ticket.state = 'pending' "
                "AND ticket.trusted_key_id IS NULL "
                "AND ticket.expires_at > now() "
                "AND station.id = ticket.workstation_id AND station.archived_at IS NULL "
                "AND station.administrative_status = 'in_operation' "
                "AND identity.workstation_id = ticket.workstation_id "
                "AND identity.state = 'prepared' AND identity.revocation_status = 'none' "
                "AND identity.ingest_authorized = FALSE "
                "RETURNING ticket.id",
                (ticket_id, workstation_id, digest),
            ).fetchone()
            if row is None:
                return False
            self._event(conn, str(row["id"]), "consumed", None)
            return True

    def cancel(self, *, ticket_id: str, workstation_id: str, actor: Actor) -> bool:
        """Manual invalidation for a pending ticket, independent of remote status."""
        with self._tx() as conn:
            row = conn.execute(
                f"UPDATE {TICKETS} SET state = 'cancelled', closed_at = now() "
                "WHERE id = %s AND workstation_id = %s AND state = 'pending' "
                "RETURNING id",
                (ticket_id, workstation_id),
            ).fetchone()
            if row is None:
                return False
            self._event(conn, str(row["id"]), "cancelled", actor.id)
            return True

    def status(self, *, ticket_id: str, workstation_id: str) -> dict | None:
        """Metadata only: no hash, secret, Keycloak grant or capability."""
        with self._tx() as conn:
            row = conn.execute(
                f"SELECT id, workstation_id, issued_at, expires_at, state, closed_at "
                f"FROM {TICKETS} WHERE id = %s AND workstation_id = %s",
                (ticket_id, workstation_id),
            ).fetchone()
            return dict(row) if row else None
