"""S2 rework — real PostgreSQL integration tests for decision atomicity.

Requires an isolated PostgreSQL: set SUPPLIES_TEST_PG_* env vars (or run the
ephemeral container documented in docs/supplier-enrichment-review-api.md).
Mock repositories are NOT accepted as proof of SQL atomicity — every
behavior here is exercised against the real engine and schema.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from app.application.services.supplier_enrichment.contracts import (
    DecisionItem,
    IdempotencyConflictError,
    ProposalRecord,
    ReviewRecord,
    ReviewRevisionConflictError,
)
from app.domain.supplier_enrichment.review_lifecycle import Decision
from app.infrastructure.persistence import migrations_runner
from app.infrastructure.persistence.supplier_enrichment_repository import (
    PostgresSupplierEnrichmentRepository,
)

NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)

pytestmark = pytest.mark.skipif(
    not os.getenv("SUPPLIES_TEST_PG_HOST"),
    reason="SUPPLIES_TEST_PG_HOST not set — isolated PostgreSQL required",
)


@pytest.fixture(scope="session")
def pg_env():
    """Point the app connection factory at the isolated test database."""
    env = {
        "PLUGINS_DB_HOST": os.environ["SUPPLIES_TEST_PG_HOST"],
        "PLUGINS_DB_PORT": os.getenv("SUPPLIES_TEST_PG_PORT", "5432"),
        "PLUGINS_DB_NAME": os.getenv("SUPPLIES_TEST_PG_NAME", "postgres"),
        "PLUGINS_DB_USER": os.getenv("SUPPLIES_TEST_PG_USER", "postgres"),
        "PLUGINS_DB_PASSWORD": os.getenv("SUPPLIES_TEST_PG_PASSWORD", "test"),
        "PLUGINS_DB_SSLMODE": "disable",
    }
    old = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    # Reset schema and apply all migrations through the real runner.
    admin = psycopg.connect(
        conninfo=(
            f"host={env['PLUGINS_DB_HOST']} port={env['PLUGINS_DB_PORT']} "
            f"dbname={env['PLUGINS_DB_NAME']} user={env['PLUGINS_DB_USER']} "
            f"password={env['PLUGINS_DB_PASSWORD']} sslmode=disable"
        ),
        autocommit=True,
    )
    admin.execute("DROP SCHEMA IF EXISTS supplies CASCADE")
    admin.close()
    migrations_runner.run_migrations()
    yield env
    for key, value in old.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture()
def repo(pg_env):
    repository = PostgresSupplierEnrichmentRepository()
    # Clean slate per test — FK-safe order.
    conn = migrations_runner.get_connection()
    with conn.cursor() as cur:
        for table in (
            "supplier_enrichment_events",
            "supplier_enrichment_decisions",
            "supplier_enrichment_decision_operations",
            "supplier_enrichment_proposals",
            "supplier_enrichment_reviews",
        ):
            cur.execute(f"DELETE FROM supplies.{table}")
    conn.commit()
    conn.close()
    return repository


def _review(**over) -> ReviewRecord:
    base = dict(
        review_id=str(uuid.uuid4()),
        supplier_code="003878",
        supplier_store="01",
        unit_context=None,
        actor_subject="22222222-2222-2222-2222-222222222222",
        source_id="FIXTURE",
        source_reference="fixture://1",
        source_retrieved_at=NOW,
        mapping_version="cnpj-sa2-v1",
        normalization_version="norm-v1",
        baseline_reference="fp",
        status="IN_REVIEW",
        revision=1,
        created_at=NOW,
        updated_at=NOW,
        expires_at=NOW + timedelta(hours=1),
    )
    base.update(over)
    return ReviewRecord(**base)


def _proposal(review_id: str, field_key: str, **over) -> ProposalRecord:
    base = dict(
        proposal_id=str(uuid.uuid4()),
        review_id=review_id,
        field_key=field_key,
        section_key="identification",
        comparison_state="DIFFERENT",
        eligibility_state="ELIGIBLE_TO_APPLY",
        eligibility_reason=None,
        source_field="company.legal_name",
        source_reference="fixture://1",
        current_value="A",
        suggested_value="B",
        decision_state="PENDING",
    )
    base.update(over)
    return ProposalRecord(**base)


def _seed(repo, fields):
    review = _review()
    proposals = [_proposal(review.review_id, f) for f in fields]
    repo.create_review(review=review, proposals=proposals)
    return review, proposals


def _count(table, where="", params=()):
    conn = migrations_runner.get_connection()
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) AS n FROM supplies.{table} {where}", params)
        n = cur.fetchone()["n"]
    conn.close()
    return n


class TestMigration:
    def test_schema_migrations_applied(self, pg_env):
        applied = migrations_runner.get_applied_migrations(
            migrations_runner.get_connection()
        )
        assert {"V001", "V002", "V003"} <= set(applied)

    def test_real_constraints(self, pg_env):
        conn = migrations_runner.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT pg_get_constraintdef(oid) AS def FROM pg_constraint
                WHERE conrelid = 'supplies.supplier_enrichment_decision_operations'::regclass
                  AND contype = 'u'
                """
            )
            ops_constraints = {r["def"] for r in cur.fetchall()}
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM pg_attribute
                WHERE attrelid = 'supplies.supplier_enrichment_decisions'::regclass
                  AND attname IN ('idempotency_key', 'request_hash')
                """
            )
            legacy_cols = cur.fetchone()["n"]
            cur.execute(
                """
                SELECT COUNT(*) AS n FROM pg_attribute
                WHERE attrelid = 'supplies.supplier_enrichment_decisions'::regclass
                  AND attname = 'operation_id' AND attnotnull
                """
            )
            op_notnull = cur.fetchone()["n"]
        conn.close()
        # Idempotency lives on the operation, never on the per-field row.
        assert ops_constraints == {
            "UNIQUE (review_id, idempotency_key)"
        }
        assert legacy_cols == 0
        assert op_notnull == 1


class TestApplyDecisions:
    def test_single_accept(self, repo):
        review, props = _seed(repo, ["supplier_name"])
        repo.apply_decisions(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.ACCEPT, reason_code=None,
            decisions=[DecisionItem(props[0].proposal_id, Decision.ACCEPT, None)],
            expected_revision=1, idempotency_key="k-1", request_hash="h1",
            new_status="DECIDED", event_type="FIELD_DECISION", decided_at=NOW,
        )
        assert _count("supplier_enrichment_decisions") == 1
        assert _count("supplier_enrichment_decision_operations") == 1
        assert repo.get_proposals(review.review_id)[0].decision_state == "ACCEPTED_FOR_DRAFT"
        assert repo.get_review(review.review_id).revision == 2

    def test_single_reject(self, repo):
        review, props = _seed(repo, ["supplier_name"])
        repo.apply_decisions(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.REJECT, reason_code="manual",
            decisions=[DecisionItem(props[0].proposal_id, Decision.REJECT, "manual")],
            expected_revision=1, idempotency_key="k-2", request_hash="h2",
            new_status="DECIDED", event_type="FIELD_DECISION", decided_at=NOW,
        )
        assert repo.get_proposals(review.review_id)[0].decision_state == "REJECTED_SUGGESTION"

    @pytest.mark.parametrize("fields", [
        ["supplier_name", "address"],
        ["supplier_name", "address", "district"],
    ])
    def test_bulk_accept_n_fields(self, repo, fields):
        """The reworked case — V002 violated UNIQUE at the second row."""
        review, props = _seed(repo, fields)
        repo.apply_decisions(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.ACCEPT, reason_code=None,
            decisions=[DecisionItem(p.proposal_id, Decision.ACCEPT, None) for p in props],
            expected_revision=1, idempotency_key="k-bulk", request_hash="hb",
            new_status="IN_REVIEW", event_type="BULK_DECISION", decided_at=NOW,
        )
        assert _count("supplier_enrichment_decisions") == len(fields)
        assert _count("supplier_enrichment_decision_operations") == 1
        assert _count("supplier_enrichment_events") == len(fields) + 1  # +created
        states = {p.decision_state for p in repo.get_proposals(review.review_id)}
        assert states == {"ACCEPTED_FOR_DRAFT"}

    @pytest.mark.parametrize("fields", [
        ["supplier_name", "address"],
        ["supplier_name", "address", "district"],
    ])
    def test_bulk_reject_n_fields(self, repo, fields):
        review, props = _seed(repo, fields)
        repo.apply_decisions(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.REJECT, reason_code=None,
            decisions=[DecisionItem(p.proposal_id, Decision.REJECT, None) for p in props],
            expected_revision=1, idempotency_key="k-rej", request_hash="hr",
            new_status="DECIDED", event_type="BULK_DECISION", decided_at=NOW,
        )
        states = {p.decision_state for p in repo.get_proposals(review.review_id)}
        assert states == {"REJECTED_SUGGESTION"}

    def test_decisions_linked_to_operation(self, repo):
        review, props = _seed(repo, ["supplier_name", "address"])
        repo.apply_decisions(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.ACCEPT, reason_code=None,
            decisions=[DecisionItem(p.proposal_id, Decision.ACCEPT, None) for p in props],
            expected_revision=1, idempotency_key="k-link", request_hash="hl",
            new_status="IN_REVIEW", event_type="BULK_DECISION", decided_at=NOW,
        )
        decisions = repo.get_decisions(review.review_id)
        assert len(decisions) == 2
        op_ids = {d.operation_id for d in decisions}
        assert len(op_ids) == 1
        assert {d.field_key for d in decisions} == {"supplier_name", "address"}


class TestRollbackAndConcurrency:
    def test_full_rollback_when_a_proposal_is_no_longer_pending(self, repo):
        review, props = _seed(repo, ["supplier_name", "address", "district"])
        # Pre-decide the second proposal directly.
        conn = migrations_runner.get_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE supplies.supplier_enrichment_proposals
                SET decision_state = 'REJECTED_SUGGESTION'
                WHERE proposal_id = %s
                """,
                (props[1].proposal_id,),
            )
        conn.commit()
        conn.close()
        with pytest.raises(ReviewRevisionConflictError):
            repo.apply_decisions(
                review_id=review.review_id, actor_subject=review.actor_subject,
                decision=Decision.ACCEPT, reason_code=None,
                decisions=[
                    DecisionItem(p.proposal_id, Decision.ACCEPT, None) for p in props
                ],
                expected_revision=1, idempotency_key="k-rb", request_hash="hrb",
                new_status="IN_REVIEW", event_type="BULK_DECISION", decided_at=NOW,
            )
        # Integral rollback — no decision, no operation, no event, no revision bump.
        assert _count("supplier_enrichment_decisions") == 0
        assert _count("supplier_enrichment_decision_operations") == 0
        assert _count("supplier_enrichment_events") == 1  # only REVIEW_CREATED
        assert repo.get_review(review.review_id).revision == 1

    def test_concurrent_same_revision_second_loses(self, repo):
        review, props = _seed(repo, ["supplier_name", "address"])
        kwargs = dict(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.ACCEPT, reason_code=None,
            expected_revision=1, event_type="BULK_DECISION", decided_at=NOW,
        )
        repo.apply_decisions(
            decisions=[DecisionItem(props[0].proposal_id, Decision.ACCEPT, None)],
            idempotency_key="k-a", request_hash="ha", new_status="IN_REVIEW",
            **kwargs,
        )
        with pytest.raises(ReviewRevisionConflictError):
            repo.apply_decisions(
                decisions=[DecisionItem(props[1].proposal_id, Decision.ACCEPT, None)],
                idempotency_key="k-b", request_hash="hb", new_status="IN_REVIEW",
                **kwargs,
            )
        assert _count("supplier_enrichment_decisions") == 1

    def test_concurrent_same_idempotency_key_blocked_by_db(self, repo):
        """Two batches racing on the same key — DB constraint is the arbiter."""
        review, props = _seed(repo, ["supplier_name", "address"])
        repo.apply_decisions(
            review_id=review.review_id, actor_subject=review.actor_subject,
            decision=Decision.ACCEPT, reason_code=None,
            decisions=[DecisionItem(props[0].proposal_id, Decision.ACCEPT, None)],
            expected_revision=1, idempotency_key="k-race", request_hash="h1",
            new_status="IN_REVIEW", event_type="BULK_DECISION", decided_at=NOW,
        )
        # Second batch reuses the key — unique violation maps to conflict.
        with pytest.raises(IdempotencyConflictError):
            repo.apply_decisions(
                review_id=review.review_id, actor_subject=review.actor_subject,
                decision=Decision.REJECT, reason_code=None,
                decisions=[DecisionItem(props[1].proposal_id, Decision.REJECT, None)],
                expected_revision=2, idempotency_key="k-race", request_hash="h2",
                new_status="IN_REVIEW", event_type="BULK_DECISION", decided_at=NOW,
            )
        # The losing batch wrote nothing.
        assert _count("supplier_enrichment_decision_operations") == 1
        assert _count("supplier_enrichment_decisions") == 1

    def test_connection_failure_mid_transaction_rolls_back(self, repo, monkeypatch):
        review, props = _seed(repo, ["supplier_name", "address", "district"])
        real_get = migrations_runner.get_connection
        calls = {"n": 0}

        class FailingCursor:
            def __init__(self, cur):
                self._cur = cur
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return self._cur.__exit__(*a)
            def execute(self, *a, **k):
                calls["n"] += 1
                if calls["n"] == 4:  # fail after revision bump + validation
                    raise psycopg.OperationalError("connection lost mid-tx")
                return self._cur.execute(*a, **k)
            def fetchone(self):
                return self._cur.fetchone()
            def fetchall(self):
                return self._cur.fetchall()
            @property
            def rowcount(self):
                return self._cur.rowcount

        class FailingConn:
            def __init__(self, conn):
                self._conn = conn
            def __enter__(self):
                return self
            def __exit__(self, *a):
                return self._conn.__exit__(*a)
            def cursor(self):
                return FailingCursor(self._conn.cursor())
            def commit(self):
                return self._conn.commit()
            def rollback(self):
                return self._conn.rollback()

        monkeypatch.setattr(
            "app.infrastructure.persistence.supplier_enrichment_repository.get_connection",
            lambda: FailingConn(real_get()),
        )
        with pytest.raises(psycopg.OperationalError):
            repo.apply_decisions(
                review_id=review.review_id, actor_subject=review.actor_subject,
                decision=Decision.ACCEPT, reason_code=None,
                decisions=[
                    DecisionItem(p.proposal_id, Decision.ACCEPT, None) for p in props
                ],
                expected_revision=1, idempotency_key="k-fail", request_hash="hf",
                new_status="IN_REVIEW", event_type="BULK_DECISION", decided_at=NOW,
            )
        assert _count("supplier_enrichment_decision_operations") == 0
        assert _count("supplier_enrichment_decisions") == 0
        assert repo.get_review(review.review_id).revision == 1
        assert {p.decision_state for p in repo.get_proposals(review.review_id)} == {"PENDING"}
