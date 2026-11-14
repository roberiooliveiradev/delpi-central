"""G2-S4-S2b-P3: inert binding of pretrusted Ed25519 challenge to one-time ticket.

Only a separately approved and pre-provisioned key may be used. This module
cannot adopt public keys or enable Keycloak, S2S, installation or remote access.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from it_portal_app.domain.workstation_bootstrap_tickets import ticket_digest
from it_portal_app.domain.workstation_device_proof import (
    DeviceProofChallenge, canonical_challenge, verify_pretrusted_device_proof,
)
from it_portal_app.infrastructure.persistence.postgres_base import PostgresRepositoryBase

T = "it_portal.workstation_bootstrap_tickets"
K = "it_portal.workstation_trusted_device_keys"
E = "it_portal.workstation_bootstrap_ticket_events"


class PostgresSignedBootstrapStore(PostgresRepositoryBase):
    def bind_pretrusted(self, challenge: DeviceProofChallenge, trusted_key_id: str) -> bool:
        """Persist challenge, only if pretrusted key exists and ticket is unbound."""
        try:
            canonical_challenge(challenge)
            key_id = str(uuid.UUID(trusted_key_id))
            if key_id != trusted_key_id or uuid.UUID(key_id).int == 0:
                return False
        except (ValueError, TypeError, AttributeError):
            return False
        # Atomic update: ticket expiry and machine eligibility must still hold.
        with self._tx() as conn:
            key = conn.execute(
                f"SELECT public_key FROM {K} WHERE id = %s AND workstation_id = %s "
                "AND state = 'trusted' FOR SHARE",
                (trusted_key_id, challenge.workstation_id),
            ).fetchone()
            if key is None:
                return False
            row = conn.execute(
                f"UPDATE {T} AS t SET trusted_key_id = %s, challenge_nonce = %s, "
                "challenge_issued_at = %s, challenge_expires_at = %s "
                "FROM it_portal.workstation_agent_identities AS i, it_portal.workstations AS w "
                "WHERE t.id = %s AND t.workstation_id = %s AND t.state = 'pending' "
                "AND t.trusted_key_id IS NULL AND t.expires_at > now() "
                "AND %s <= now() + INTERVAL '30 seconds' "
                "AND %s > now() AND %s <= t.expires_at "
                "AND i.workstation_id = t.workstation_id AND i.state = 'prepared' "
                "AND i.revocation_status = 'none' AND i.ingest_authorized = FALSE "
                "AND w.id = t.workstation_id AND w.archived_at IS NULL "
                "AND w.administrative_status = 'in_operation' "
                "RETURNING t.id",
                (trusted_key_id, challenge.nonce, challenge.issued_at, challenge.expires_at,
                 challenge.ticket_id, challenge.workstation_id,
                 challenge.issued_at, challenge.expires_at, challenge.expires_at),
            ).fetchone()
            return row is not None

    def verify_and_spend(self, challenge: DeviceProofChallenge, *,
                         opaque_token: str, signature: str) -> bool:
        """Transactionally validate key, original challenge and token, then consume.

        No route calls this. The return is ONLY proof of pretrusted key possession,
        not device hardware attestation and never a grant of any capability.
        """
        try:
            canonical_challenge(challenge)
            digest = ticket_digest(opaque_token)
        except (ValueError, TypeError, AttributeError):
            return False
        with self._tx() as conn:
            # Lock ticket first. This serializes all replays and cancellation.
            row = conn.execute(
                f"SELECT t.trusted_key_id, t.challenge_nonce, t.challenge_issued_at, "
                "t.challenge_expires_at, t.token_digest, t.expires_at, t.state, "
                "i.state AS identity_state, i.revocation_status, i.ingest_authorized, "
                "w.archived_at, w.administrative_status "
                f"FROM {T} AS t "
                "JOIN it_portal.workstation_agent_identities AS i ON i.workstation_id = t.workstation_id "
                "JOIN it_portal.workstations AS w ON w.id = t.workstation_id "
                "WHERE t.id = %s AND t.workstation_id = %s FOR UPDATE OF t",
                (challenge.ticket_id, challenge.workstation_id),
            ).fetchone()
            if row is None or row["state"] != "pending" or row["trusted_key_id"] is None:
                return False
            if (row["token_digest"].strip() != digest or row["expires_at"] <= datetime.now(timezone.utc)
                    or row["challenge_nonce"] != challenge.nonce
                    or row["challenge_issued_at"] != challenge.issued_at
                    or row["challenge_expires_at"] != challenge.expires_at
                    or row["identity_state"] != "prepared" or row["revocation_status"] != "none"
                    or row["ingest_authorized"] is not False
                    or row["archived_at"] is not None
                    or row["administrative_status"] != "in_operation"):
                return False
            # Lock the key against concurrent revocation before verifying.
            trusted = conn.execute(
                f"SELECT public_key FROM {K} "
                "WHERE id = %s AND workstation_id = %s AND state = 'trusted' FOR SHARE",
                (str(row["trusted_key_id"]), challenge.workstation_id),
            ).fetchone()
            if trusted is None:
                return False
            now = datetime.now(timezone.utc)
            if not verify_pretrusted_device_proof(
                challenge, signature, bytes(trusted["public_key"]),
                ticket_id=challenge.ticket_id, workstation_id=challenge.workstation_id,
                now=now,
            ):
                return False
            updated = conn.execute(
                f"UPDATE {T} SET state = 'consumed', closed_at = now() "
                "WHERE id = %s AND state = 'pending' AND expires_at > now() "
                "AND challenge_expires_at > now() AND trusted_key_id = %s RETURNING id",
                (challenge.ticket_id, str(row["trusted_key_id"])),
            ).fetchone()
            if updated is None:
                return False
            conn.execute(
                f"INSERT INTO {E} (id, ticket_id, event_type) VALUES (%s, %s, 'consumed')",
                (str(uuid.uuid4()), challenge.ticket_id),
            )
            return True
