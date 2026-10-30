"""V005 — real PostgreSQL integration tests for SURI execute claims.

Requires an isolated PostgreSQL: set SUPPLIES_TEST_PG_* env vars (same
convention as test_supplier_enrichment_repository_pg). Mock stores are
NOT accepted as proof of atomicity — the UNIQUE claim is exercised
against the real engine and schema.
"""

from __future__ import annotations

import os
from datetime import timedelta

import psycopg
import pytest

from app.infrastructure.persistence import migrations_runner
from app.infrastructure.persistence.suri_execute_operations_repository import (
    PostgresSuriExecuteOperationsRepository,
)

pytestmark = pytest.mark.skipif(
    not os.getenv("SUPPLIES_TEST_PG_HOST"),
    reason="SUPPLIES_TEST_PG_HOST not set — isolated PostgreSQL required",
)


@pytest.fixture(scope="session")
def pg_env():
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
    admin = psycopg.connect(
        conninfo=(
            f"host={env['PLUGINS_DB_HOST']} port={env['PLUGINS_DB_PORT']} "
            f"dbname={env['PLUGINS_DB_NAME']} user={env['PLUGINS_DB_USER']} "
            f"password={env['PLUGINS_DB_PASSWORD']} sslmode=disable"
        ),
        autocommit=True,
    )
    with admin.cursor() as cur:
        cur.execute("DROP SCHEMA IF EXISTS supplies CASCADE")
    migrations_runner.run_migrations()
    yield env
    for key, value in old.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


@pytest.fixture()
def repo(pg_env):
    return PostgresSuriExecuteOperationsRepository(ttl=timedelta(hours=24))


def _claim(repo, *, key="k1", actor="u1", action="create", h="hash-a"):
    return repo.claim(
        actor_subject=actor,
        entity="suppliers",
        action=action,
        idempotency_key=key,
        payload_hash=h,
        correlation_id="corr-1",
    )


def test_claim_replay_conflict_in_progress(repo):
    first = _claim(repo)
    assert first.kind == "claimed" and first.operation_id

    # Concurrent same-key caller while still in flight.
    second = _claim(repo)
    assert second.kind == "in_progress"

    # Same key, different payload fingerprint → conflict.
    conflict = _claim(repo, h="hash-b")
    assert conflict.kind == "conflict"

    # Complete → same key+hash replays the stored result.
    repo.complete(
        operation_id=first.operation_id,
        result={"outcome": "confirmed", "operation_id": "op-1"},
    )
    replay = _claim(repo)
    assert replay.kind == "replay"
    assert replay.result["outcome"] == "confirmed"


def test_claim_scoped_by_actor_and_action(repo):
    assert _claim(repo, actor="u-a", key="k").kind == "claimed"
    assert _claim(repo, actor="u-b", key="k").kind == "claimed"
    assert _claim(repo, actor="u-a", key="k", action="update").kind == "claimed"
    assert _claim(repo, actor="u-a", key="k").kind == "in_progress"


def test_expired_rows_are_garbage_collected(repo, pg_env):
    claim = _claim(repo, key="gc-1")
    assert claim.kind == "claimed"
    with migrations_runner.get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE supplies.suri_execute_operations "
                "SET expires_at = NOW() - INTERVAL '1 hour' "
                "WHERE operation_id = %s",
                (claim.operation_id,),
            )
        conn.commit()
    assert repo.gc_expired() == 1
    reclaim = _claim(repo, key="gc-1")
    assert reclaim.kind == "claimed"
