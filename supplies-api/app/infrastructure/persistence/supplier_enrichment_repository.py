"""Postgres repository for supplier enrichment reviews (S2).

Owns transactions: decision batches are applied atomically — proposal
states, decision rows, audit events and the revision bump either all
commit or none do. Optimistic concurrency is enforced by updating the
review row guarded on the expected revision.
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Sequence

import psycopg

from app.application.services.supplier_enrichment.contracts import (
    DecisionItem,
    DecisionRecord,
    IdempotencyConflictError,
    OperationRecord,
    ProposalRecord,
    ReviewRecord,
    ReviewRevisionConflictError,
)
from app.domain.supplier_enrichment.review_lifecycle import Decision
from app.infrastructure.persistence.migrations_runner import get_connection


class PostgresSupplierEnrichmentRepository:
    """SQL adapter implementing the SupplierEnrichmentReviewRepository port."""

    # -- creation ---------------------------------------------------------

    def create_review(
        self,
        *,
        review: ReviewRecord,
        proposals: Sequence[ProposalRecord],
    ) -> ReviewRecord:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO supplies.supplier_enrichment_reviews (
                        review_id, supplier_code, supplier_store, unit_context,
                        actor_subject, source_id, source_reference,
                        source_retrieved_at, mapping_version,
                        normalization_version, baseline_reference, status,
                        revision, created_at, updated_at, expires_at
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        review.review_id, review.supplier_code,
                        review.supplier_store, review.unit_context,
                        review.actor_subject, review.source_id,
                        review.source_reference, review.source_retrieved_at,
                        review.mapping_version, review.normalization_version,
                        review.baseline_reference, review.status,
                        review.revision, review.created_at, review.updated_at,
                        review.expires_at,
                    ),
                )
                for proposal in proposals:
                    cur.execute(
                        """
                        INSERT INTO supplies.supplier_enrichment_proposals (
                            proposal_id, review_id, field_key, section_key,
                            comparison_state, eligibility_state,
                            eligibility_reason, source_field, source_reference,
                            current_value, suggested_value, decision_state
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            proposal.proposal_id, proposal.review_id,
                            proposal.field_key, proposal.section_key,
                            proposal.comparison_state, proposal.eligibility_state,
                            proposal.eligibility_reason, proposal.source_field,
                            proposal.source_reference, proposal.current_value,
                            proposal.suggested_value, proposal.decision_state,
                        ),
                    )
                cur.execute(
                    """
                    INSERT INTO supplies.supplier_enrichment_events (
                        review_id, actor_subject, event_type, metadata
                    ) VALUES (%s, %s, %s, %s)
                    """,
                    (
                        review.review_id, review.actor_subject,
                        "REVIEW_CREATED", None,
                    ),
                )
            conn.commit()
        return review

    # -- queries -----------------------------------------------------------

    def get_review(self, review_id: str) -> ReviewRecord | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT review_id, supplier_code, supplier_store, unit_context,
                           actor_subject, source_id, source_reference,
                           source_retrieved_at, mapping_version,
                           normalization_version, baseline_reference, status,
                           revision, created_at, updated_at, expires_at
                    FROM supplies.supplier_enrichment_reviews
                    WHERE review_id = %s
                    """,
                    (review_id,),
                )
                row = cur.fetchone()
        return _review(row) if row else None

    def list_reviews(
        self,
        *,
        supplier_code: str,
        supplier_store: str,
        actor_subject: str,
        limit: int,
        offset: int,
    ) -> tuple[list[ReviewRecord], int]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) AS total
                    FROM supplies.supplier_enrichment_reviews
                    WHERE supplier_code = %s AND supplier_store = %s
                      AND actor_subject = %s
                    """,
                    (supplier_code, supplier_store, actor_subject),
                )
                total = int(cur.fetchone()["total"])
                cur.execute(
                    """
                    SELECT review_id, supplier_code, supplier_store, unit_context,
                           actor_subject, source_id, source_reference,
                           source_retrieved_at, mapping_version,
                           normalization_version, baseline_reference, status,
                           revision, created_at, updated_at, expires_at
                    FROM supplies.supplier_enrichment_reviews
                    WHERE supplier_code = %s AND supplier_store = %s
                      AND actor_subject = %s
                    ORDER BY created_at DESC, review_id DESC
                    LIMIT %s OFFSET %s
                    """,
                    (supplier_code, supplier_store, actor_subject, limit, offset),
                )
                rows = cur.fetchall()
        return [_review(row) for row in rows], total

    def get_proposals(self, review_id: str) -> list[ProposalRecord]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT proposal_id, review_id, field_key, section_key,
                           comparison_state, eligibility_state,
                           eligibility_reason, source_field, source_reference,
                           current_value, suggested_value, decision_state
                    FROM supplies.supplier_enrichment_proposals
                    WHERE review_id = %s
                    ORDER BY field_key
                    """,
                    (review_id,),
                )
                rows = cur.fetchall()
        return [_proposal(row) for row in rows]

    def get_decisions(self, review_id: str) -> list[DecisionRecord]:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT d.decision_id, d.review_id, d.proposal_id,
                           d.operation_id, p.field_key, d.actor_subject,
                           d.decision, o.reason_code, d.decided_at,
                           o.review_revision
                    FROM supplies.supplier_enrichment_decisions d
                    JOIN supplies.supplier_enrichment_decision_operations o
                        ON o.operation_id = d.operation_id
                    JOIN supplies.supplier_enrichment_proposals p
                        ON p.proposal_id = d.proposal_id
                    WHERE d.review_id = %s
                    ORDER BY d.decided_at, d.decision_id
                    """,
                    (review_id,),
                )
                rows = cur.fetchall()
        return [_decision(row) for row in rows]

    def find_operation_by_idempotency_key(
        self, *, review_id: str, idempotency_key: str
    ) -> OperationRecord | None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT operation_id, review_id, actor_subject, decision,
                           reason_code, idempotency_key, request_hash,
                           review_revision, decided_at
                    FROM supplies.supplier_enrichment_decision_operations
                    WHERE review_id = %s AND idempotency_key = %s
                    """,
                    (review_id, idempotency_key),
                )
                row = cur.fetchone()
        return _operation(row) if row else None

    # -- mutations ----------------------------------------------------------

    def apply_decisions(
        self,
        *,
        review_id: str,
        actor_subject: str,
        decision: Decision,
        reason_code: str | None,
        decisions: Sequence[DecisionItem],
        expected_revision: int,
        idempotency_key: str,
        request_hash: str,
        new_status: str,
        event_type: str,
        decided_at: datetime,
    ) -> tuple[ReviewRecord, list[ProposalRecord]]:
        """Atomic decision batch guarded by the expected review revision.

        One ``decision_operations`` row carries the request identity
        (idempotency key + hash); N ``decisions`` rows link each field to
        that operation. Revision bump, proposal updates, decision rows and
        audit events all commit in the same transaction — any failure
        rolls back everything.
        """
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE supplies.supplier_enrichment_reviews
                    SET status = %s, revision = revision + 1, updated_at = NOW()
                    WHERE review_id = %s AND revision = %s
                    """,
                    (new_status, review_id, expected_revision),
                )
                if cur.rowcount != 1:
                    conn.rollback()
                    raise ReviewRevisionConflictError(
                        f"expected revision {expected_revision}"
                    )
                # Validate every proposal is still pending BEFORE the first
                # decision row is written — the batch stays atomic.
                pending_ids = {item.proposal_id for item in decisions}
                for item in decisions:
                    cur.execute(
                        """
                        SELECT proposal_id FROM supplies.supplier_enrichment_proposals
                        WHERE proposal_id = %s AND review_id = %s
                          AND decision_state = 'PENDING'
                        """,
                        (item.proposal_id, review_id),
                    )
                    if cur.fetchone() is None:
                        conn.rollback()
                        raise ReviewRevisionConflictError(
                            "proposal no longer pending"
                        )
                try:
                    cur.execute(
                        """
                        INSERT INTO supplies.supplier_enrichment_decision_operations (
                            review_id, actor_subject, decision, reason_code,
                            idempotency_key, request_hash, review_revision,
                            decided_at
                        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING operation_id
                        """,
                        (
                            review_id, actor_subject, decision.value,
                            reason_code, idempotency_key, request_hash,
                            expected_revision, decided_at,
                        ),
                    )
                except psycopg.errors.UniqueViolation:
                    conn.rollback()
                    raise IdempotencyConflictError(idempotency_key)
                operation_id = str(cur.fetchone()["operation_id"])
                for item in decisions:
                    if item.proposal_id not in pending_ids:
                        conn.rollback()
                        raise ReviewRevisionConflictError("decision set changed")
                    cur.execute(
                        """
                        UPDATE supplies.supplier_enrichment_proposals
                        SET decision_state = %s
                        WHERE proposal_id = %s AND review_id = %s
                          AND decision_state = 'PENDING'
                        """,
                        (_decision_state(item.decision), item.proposal_id, review_id),
                    )
                    if cur.rowcount != 1:
                        conn.rollback()
                        raise ReviewRevisionConflictError(
                            "proposal no longer pending"
                        )
                    cur.execute(
                        """
                        INSERT INTO supplies.supplier_enrichment_decisions (
                            review_id, proposal_id, operation_id, actor_subject,
                            decision, decided_at
                        ) VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            review_id, item.proposal_id, operation_id,
                            actor_subject, item.decision.value, decided_at,
                        ),
                    )
                    cur.execute(
                        """
                        INSERT INTO supplies.supplier_enrichment_events (
                            review_id, actor_subject, event_type, metadata
                        ) VALUES (%s,%s,%s,%s)
                        """,
                        (
                            review_id, actor_subject, event_type,
                            json.dumps(
                                {
                                    "operation_id": operation_id,
                                    "proposal_id": item.proposal_id,
                                    "decision": item.decision.value,
                                    "reason_code": item.reason_code,
                                }
                            ),
                        ),
                    )
            conn.commit()
        review = self.get_review(review_id)
        assert review is not None
        return review, self.get_proposals(review_id)

    def mark_status(
        self,
        *,
        review_id: str,
        status: str,
        expected_revision: int,
    ) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE supplies.supplier_enrichment_reviews
                    SET status = %s, revision = revision + 1, updated_at = NOW()
                    WHERE review_id = %s AND revision = %s
                    """,
                    (status, review_id, expected_revision),
                )
                if cur.rowcount != 1:
                    conn.rollback()
                    raise ReviewRevisionConflictError(
                        f"expected revision {expected_revision}"
                    )
            conn.commit()

    def append_event(
        self,
        *,
        review_id: str,
        actor_subject: str | None,
        event_type: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO supplies.supplier_enrichment_events (
                        review_id, actor_subject, event_type, metadata
                    ) VALUES (%s,%s,%s,%s)
                    """,
                    (
                        review_id, actor_subject, event_type,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
            conn.commit()


# --- row mapping ------------------------------------------------------------


def _decision_state(decision) -> str:
    from app.domain.supplier_enrichment.review_lifecycle import DECISION_OUTCOME

    return DECISION_OUTCOME[decision].value


def _review(row: dict[str, Any]) -> ReviewRecord:
    return ReviewRecord(
        review_id=str(row["review_id"]),
        supplier_code=row["supplier_code"],
        supplier_store=row["supplier_store"],
        unit_context=row["unit_context"],
        actor_subject=str(row["actor_subject"]),
        source_id=row["source_id"],
        source_reference=row["source_reference"],
        source_retrieved_at=row["source_retrieved_at"],
        mapping_version=row["mapping_version"],
        normalization_version=row["normalization_version"],
        baseline_reference=row["baseline_reference"],
        status=row["status"],
        revision=int(row["revision"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        expires_at=row["expires_at"],
    )


def _proposal(row: dict[str, Any]) -> ProposalRecord:
    return ProposalRecord(
        proposal_id=str(row["proposal_id"]),
        review_id=str(row["review_id"]),
        field_key=row["field_key"],
        section_key=row["section_key"],
        comparison_state=row["comparison_state"],
        eligibility_state=row["eligibility_state"],
        eligibility_reason=row["eligibility_reason"],
        source_field=row["source_field"],
        source_reference=row["source_reference"],
        current_value=row["current_value"],
        suggested_value=row["suggested_value"],
        decision_state=row["decision_state"],
    )


def _decision(row: dict[str, Any]) -> DecisionRecord:
    return DecisionRecord(
        decision_id=str(row["decision_id"]),
        review_id=str(row["review_id"]),
        proposal_id=str(row["proposal_id"]),
        operation_id=str(row["operation_id"]),
        field_key=row["field_key"],
        actor_subject=str(row["actor_subject"]),
        decision=row["decision"],
        reason_code=row["reason_code"],
        decided_at=row["decided_at"],
        review_revision=int(row["review_revision"]),
    )


def _operation(row: dict[str, Any]) -> OperationRecord:
    return OperationRecord(
        operation_id=str(row["operation_id"]),
        review_id=str(row["review_id"]),
        actor_subject=str(row["actor_subject"]),
        decision=row["decision"],
        reason_code=row["reason_code"],
        idempotency_key=row["idempotency_key"],
        request_hash=row["request_hash"],
        review_revision=int(row["review_revision"]),
        decided_at=row["decided_at"],
    )
