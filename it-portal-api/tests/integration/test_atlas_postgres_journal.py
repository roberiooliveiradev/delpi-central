"""P2.2e: real PostgreSQL journal tests against disposable GitHub-hosted CI DB.

NOT for the application DB. This suite skips without explicit isolated-CI gate.
It must never run via a production API, migration runner or MCP tool.
"""
from __future__ import annotations

import hashlib
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest

try:
    import psycopg
    from psycopg.conninfo import conninfo_to_dict
except ImportError:
    if os.environ.get("ATLAS_DISPOSABLE_PG") == "true":
        raise
    pytest.skip("psycopg is required only for disposable PostgreSQL integration", allow_module_level=True)

from it_portal_app.infrastructure.persistence.atlas_deploy_journal import (
    JournalRejected,
    PrepareIntent,
    issue_challenge,
    store_prepared,
)

_SCHEMA = Path(__file__).resolve().parents[3] / (
    "docs/12-roadmap-e-evolucao/mcp-linux-control/05-atlas-p22d-candidate-schema.sql"
)


@pytest.fixture(scope="module")
def ci_dsn():
    """Only an explicit, loopback CI database with a known disposable identity."""
    dsn = os.environ.get("ATLAS_ISOLATED_PG_DSN")
    if not (os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("ATLAS_DISPOSABLE_PG") == "true" and dsn):
        pytest.skip("PostgreSQL integration requires explicit disposable CI database")
    try:
        data = conninfo_to_dict(dsn)
    except Exception:
        pytest.fail("invalid disposable PostgreSQL DSN")
    if (data.get("host") not in ("127.0.0.1", "localhost")
            or data.get("dbname") != "atlas_ci_disposable"
            or data.get("user") != "atlas_ci"
            or data.get("port", "5432") != "5432"):
        pytest.fail("refusing non-disposable or non-loopback PostgreSQL target")
    return dsn


@pytest.fixture(scope="module")
def schema_ready(ci_dsn):
    """No DROP or migrations. Runner gives this CI service a fresh database."""
    with psycopg.connect(ci_dsn, autocommit=True, connect_timeout=5) as conn:
        result = conn.execute("SELECT 1 FROM pg_namespace WHERE nspname = 'it_portal'").fetchone()
        if result:
            pytest.fail("disposable test DB was not empty; refusing to modify it")
        conn.execute("CREATE SCHEMA it_portal")
        conn.execute(_SCHEMA.read_text(encoding="utf-8"))
        assert conn.execute(
            "SELECT count(*) FROM information_schema.tables "
            "WHERE table_schema='it_portal'"
        ).fetchone()[0] == 3
    return ci_dsn


@pytest.fixture()
def pg(schema_ready):
    with psycopg.connect(schema_ready, autocommit=True, connect_timeout=5) as conn:
        conn.execute(
            "TRUNCATE it_portal.atlas_deploy_events, it_portal.atlas_deploy_proposals, "
            "it_portal.atlas_deploy_challenges"
        )
        yield conn


def intent(**kwargs):
    base = PrepareIntent(
        requester_subject="11111111-2222-4333-8444-555555555555",
        request_id="01234567-89ab-4def-8abc-0123456789ab",
        environment="hml", service_id="it-portal-api",
        target_sha="a" * 40, base_sha="b" * 40, proposal_hash="c" * 64,
    )
    return replace(base, **kwargs)


def _counts(conn):
    return tuple(conn.execute(f"SELECT count(*) FROM it_portal.{table}").fetchone()[0]
                 for table in ("atlas_deploy_challenges", "atlas_deploy_proposals", "atlas_deploy_events"))


def test_real_postgres_create_replay_and_event_once(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    digest = hashlib.sha256(bytes.fromhex(nonce)).hexdigest()
    first = store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    second = store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    assert first.proposal_id == second.proposal_id
    assert first.result == "created_pending_approval"
    assert second.result == "replay_pending_approval"
    assert _counts(pg) == (1, 1, 1)
    used, saved = pg.execute(
        "SELECT consumed_at, challenge_digest FROM it_portal.atlas_deploy_challenges"
    ).fetchone()
    assert used is not None and saved == digest


def test_invalid_nonce_fails_before_insert_and_preserves_database(pg):
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(), signed_receipt_challenge="f" * 64)
    assert _counts(pg) == (0, 0, 0)


def test_replay_payload_conflict_preserves_original(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    with pytest.raises(JournalRejected, match="IDEMPOTENCY_PAYLOAD_CONFLICT"):
        store_prepared(pg, intent=intent(target_sha="d" * 40), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 1, 1)


def test_one_shot_challenge_for_different_request(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(request_id=str(uuid4())), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 1, 1)


def test_expired_challenge_is_not_consumed(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    # Keep CHECK expiration <= issued +90sec; only a disposable CI DB.
    pg.execute(
        "UPDATE it_portal.atlas_deploy_challenges SET "
        "issued_at=clock_timestamp()-interval '120 seconds', "
        "expires_at=clock_timestamp()-interval '60 seconds'"
    )
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 0, 0)


def test_parallel_same_request_serializes_to_one_proposal(pg, schema_ready):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="it-portal-api")
    start = Barrier(2)

    def writer():
        with psycopg.connect(schema_ready, autocommit=True, connect_timeout=5) as conn:
            start.wait(timeout=5)
            return store_prepared(conn, intent=intent(), signed_receipt_challenge=nonce)

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(writer) for _ in range(2)]
        outcomes = [f.result(timeout=15) for f in futures]
    assert len({r.proposal_id for r in outcomes}) == 1
    assert {r.result for r in outcomes} == {
        "created_pending_approval", "replay_pending_approval",
    }
    assert _counts(pg) == (1, 1, 1)


def test_partial_invalid_attempt_does_not_leave_event(pg):
    nonce = issue_challenge(pg, requester_subject=intent().requester_subject,
                            environment="hml", service_id="gateway")
    with pytest.raises(JournalRejected, match="CHALLENGE_MISSING_OR_CONSUMED"):
        store_prepared(pg, intent=intent(), signed_receipt_challenge=nonce)
    assert _counts(pg) == (1, 0, 0)
