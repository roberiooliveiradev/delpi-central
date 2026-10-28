"""ComexAnalysisRepository unit tests — shared-catalog concurrency.

The S7 shared catalog must never duplicate a row: two concurrent adds
of the same NCM race through ``SELECT`` (both miss) and then through
``INSERT`` — the loser hits the UNIQUE constraint and must receive the
winner's row flagged ``_existing`` instead of an unhandled error.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from psycopg.errors import UniqueViolation

from app.infrastructure.persistence.comex_analysis_repository import (
    ComexAnalysisRepository,
)

_REPO = "app.infrastructure.persistence.comex_analysis_repository"


def _row(**over):
    base = {
        "governance_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "ncm_code": "74081190",
        "ncm_version": None,
        "description": None,
        "family_code": None,
        "product_codes": "[]",
        "status": "candidate",
        "notes": None,
        "requested_by": "22222222-2222-2222-2222-222222222222",
        "requested_at": "2026-10-28T00:00:00+00:00",
        "decided_by": None,
        "decided_at": None,
        "decision_notes": None,
        "revision": 1,
        "created_at": "2026-10-28T00:00:00+00:00",
        "updated_at": "2026-10-28T00:00:00+00:00",
    }
    base.update(over)
    return base


def _conn_with_cursor(cur):
    conn = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cur
    conn.cursor.return_value.__exit__.return_value = False
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = False
    return conn


def test_concurrent_insert_conflict_returns_existing_row():
    repo = ComexAnalysisRepository()
    cur = MagicMock()
    calls = {"n": 0}

    def execute(sql, params=None):
        calls["n"] += 1
        if "INSERT" in sql:
            raise UniqueViolation("duplicate key value")
        return cur

    cur.execute = execute
    # fetchone: first SELECT misses, post-rollback SELECT finds the row.
    cur.fetchone.side_effect = [None, _row()]
    conn = _conn_with_cursor(cur)

    with patch(f"{_REPO}.get_connection", return_value=conn):
        out = repo.create_governance(
            record={
                "ncm_code": "74081190",
                "status": "candidate",
                "product_codes": [],
                "requested_by": "22222222-2222-2222-2222-222222222222",
            }
        )

    assert out["_existing"] is True
    assert out["ncm_code"] == "74081190"
    conn.rollback.assert_called_once()


def test_first_insert_wins_and_commits_audit():
    repo = ComexAnalysisRepository()
    cur = MagicMock()
    cur.fetchone.side_effect = [None, _row()]
    conn = _conn_with_cursor(cur)

    with patch(f"{_REPO}.get_connection", return_value=conn):
        out = repo.create_governance(
            record={
                "ncm_code": "74081190",
                "status": "candidate",
                "product_codes": [],
                "requested_by": "22222222-2222-2222-2222-222222222222",
            }
        )

    assert "_existing" not in out
    assert out["status"] == "candidate"
    conn.commit.assert_called_once()
