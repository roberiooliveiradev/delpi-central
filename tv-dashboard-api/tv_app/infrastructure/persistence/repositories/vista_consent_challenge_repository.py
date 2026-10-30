"""VISTA consent challenge store (SEMANTIC_TOOLS_V1, D-5).

Server-issued authorization objects bound to (actor, proposal, sealed
plan hash, target ref, action, expiry, origin channel). Lifecycle:

    PENDING → APPROVED → CONSUMED
                 ↘ EXPIRED | REVOKED

Pattern reused from CLARA's consent challenge (controllership_finance
V014) — implemented locally in the VISTA bounded context: proposals
live in the governed proposal store, so ``proposal_id`` is TEXT and
plan integrity is enforced through ``plan_hash`` (proposal.content_hash).

The Postgres adapter owns the canonical table; the in-memory adapter is
the test seam (same pattern as ``InMemoryIdempotencyRepository``).
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from psycopg.types.json import Jsonb

from tv_app.infrastructure.persistence.plugins_postgres_connection import (
    get_connection,
)

_SCHEMA = "tv_dashboard"
_TABLE = f"{_SCHEMA}.vista_consent_challenge"


def _q() -> str:
    return _TABLE


class VistaConsentChallengeRepository:
    """Canonical Postgres store for consent challenges."""

    # -- issue (PREPARE) --------------------------------------------------

    def issue_for_proposal(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        plan_hash: str,
        target_ref: str,
        action: str,
        origin: str,
        expires_at: datetime,
        correlation_id: str | None = None,
    ) -> dict | None:
        """Idempotent: a PENDING challenge per proposal is reused."""
        with get_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        INSERT INTO {_q()}
                            (proposal_id, actor_sub, plan_hash, target_ref,
                             action, origin, expires_at, correlation_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        ON CONFLICT (proposal_id) WHERE status = 'PENDING'
                        DO NOTHING
                        RETURNING *
                        """,
                        (
                            proposal_id,
                            actor_sub,
                            plan_hash,
                            target_ref,
                            action,
                            origin,
                            expires_at,
                            correlation_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        cur.execute(
                            f"""
                            SELECT * FROM {_q()}
                             WHERE proposal_id = %s AND status = 'PENDING'
                            """,
                            (proposal_id,),
                        )
                        row = cur.fetchone()
                    return dict(row) if row is not None else None

    # -- reads ------------------------------------------------------------

    def get_by_id(self, *, challenge_id: str) -> dict | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"SELECT * FROM {_q()} WHERE challenge_id = %s",
                    (challenge_id,),
                )
                row = cur.fetchone()
        return dict(row) if row is not None else None

    def latest_for_proposal(self, *, proposal_id: str) -> dict | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"""
                    SELECT * FROM {_q()}
                     WHERE proposal_id = %s
                     ORDER BY created_at DESC
                     LIMIT 1
                    """,
                    (proposal_id,),
                )
                row = cur.fetchone()
        return dict(row) if row is not None else None

    # -- approve (human channel) -------------------------------------------

    def approve(
        self,
        *,
        challenge_id: str,
        actor_sub: str,
        plan_hash: str,
        token_jti: str | None,
        token_iat: datetime | None,
        consent_record: dict,
    ) -> dict | None:
        """PENDING→APPROVED in one transaction, enforcing the binding.

        Returns the updated row, or ``None`` when the challenge is not
        PENDING or its binding does not match (caller maps the honest
        typed error — never silently approves).
        """
        with get_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        SELECT * FROM {_q()}
                         WHERE challenge_id = %s
                         FOR UPDATE
                        """,
                        (challenge_id,),
                    )
                    challenge = cur.fetchone()
                    if challenge is None:
                        return None
                    if challenge["status"] != "PENDING":
                        return None
                    if (
                        challenge["actor_sub"] != actor_sub
                        or challenge["plan_hash"] != plan_hash
                        or challenge["expires_at"]
                        < datetime.now(timezone.utc)
                    ):
                        return None
                    cur.execute(
                        f"""
                        UPDATE {_q()}
                           SET status = 'APPROVED',
                               approved_at = now(),
                               approved_by = %s,
                               approved_token_jti = %s,
                               approved_token_iat = %s,
                               consent_record = %s
                         WHERE challenge_id = %s
                        RETURNING *
                        """,
                        (
                            actor_sub,
                            token_jti,
                            token_iat,
                            Jsonb(consent_record),
                            challenge_id,
                        ),
                    )
                    updated = cur.fetchone()
                    return dict(updated) if updated is not None else None

    # -- consume (commit) ---------------------------------------------------

    def consume_approved(
        self, *, challenge_id: str, proposal_id: str, actor_sub: str
    ) -> dict | None:
        """APPROVED→CONSUMED single-use transition with binding check."""
        with get_connection() as conn:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(
                        f"""
                        UPDATE {_q()}
                           SET status = 'CONSUMED', consumed_at = now()
                         WHERE challenge_id = %s
                           AND proposal_id = %s
                           AND actor_sub = %s
                           AND status = 'APPROVED'
                        RETURNING *
                        """,
                        (challenge_id, proposal_id, actor_sub),
                    )
                    row = cur.fetchone()
                    return dict(row) if row is not None else None


class InMemoryVistaConsentChallengeRepository:
    """Deterministic test double — same transitions and binding rules."""

    def __init__(self) -> None:
        self._rows: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def issue_for_proposal(
        self,
        *,
        proposal_id: str,
        actor_sub: str,
        plan_hash: str,
        target_ref: str,
        action: str,
        origin: str,
        expires_at: datetime,
        correlation_id: str | None = None,
    ) -> dict:
        with self._lock:
            for row in self._rows.values():
                if row["proposal_id"] == proposal_id and row["status"] == "PENDING":
                    return row
            row = {
                "challenge_id": str(uuid.uuid4()),
                "proposal_id": proposal_id,
                "actor_sub": actor_sub,
                "plan_hash": plan_hash,
                "target_ref": target_ref,
                "action": action,
                "status": "PENDING",
                "origin": origin,
                "correlation_id": correlation_id,
                "approved_by": None,
                "approved_token_jti": None,
                "approved_token_iat": None,
                "consent_record": None,
                "created_at": datetime.now(timezone.utc),
                "approved_at": None,
                "consumed_at": None,
                "expires_at": expires_at,
            }
            self._rows[row["challenge_id"]] = row
            return row

    def get_by_id(self, *, challenge_id: str) -> dict | None:
        with self._lock:
            return self._rows.get(str(challenge_id))

    def latest_for_proposal(self, *, proposal_id: str) -> dict | None:
        with self._lock:
            rows = [
                r for r in self._rows.values() if r["proposal_id"] == proposal_id
            ]
            if not rows:
                return None
            return max(rows, key=lambda r: r["created_at"])

    def approve(
        self,
        *,
        challenge_id: str,
        actor_sub: str,
        plan_hash: str,
        token_jti: str | None,
        token_iat: datetime | None,
        consent_record: dict,
    ) -> dict | None:
        with self._lock:
            row = self._rows.get(str(challenge_id))
            if row is None or row["status"] != "PENDING":
                return None
            if (
                row["actor_sub"] != actor_sub
                or row["plan_hash"] != plan_hash
                or row["expires_at"] < datetime.now(timezone.utc)
            ):
                return None
            row["status"] = "APPROVED"
            row["approved_at"] = datetime.now(timezone.utc)
            row["approved_by"] = actor_sub
            row["approved_token_jti"] = token_jti
            row["approved_token_iat"] = token_iat
            row["consent_record"] = consent_record
            return row

    def consume_approved(
        self, *, challenge_id: str, proposal_id: str, actor_sub: str
    ) -> dict | None:
        with self._lock:
            row = self._rows.get(str(challenge_id))
            if (
                row is None
                or row["proposal_id"] != proposal_id
                or row["actor_sub"] != actor_sub
                or row["status"] != "APPROVED"
            ):
                return None
            row["status"] = "CONSUMED"
            row["consumed_at"] = datetime.now(timezone.utc)
            return row


_REPO = VistaConsentChallengeRepository()


def get_vista_consent_challenge_repository() -> VistaConsentChallengeRepository:
    return _REPO
