"""Schema / migration — integration-tracking (static checks)."""

from __future__ import annotations

from pathlib import Path

PLUGIN_SLUG = "integration-tracking"
_MIGRATIONS = (
    Path(__file__).resolve().parents[1] / "migrations" / "plugins" / PLUGIN_SLUG
)
MIGRATION = _MIGRATIONS / "V001__integration_operations.sql"

_STATUSES = [
    "CREATED",
    "SENDING",
    "ACKNOWLEDGED",
    "CONFIRMED",
    "REJECTED",
    "FAILED_PRE_SEND",
    "UNKNOWN",
    "RECONCILIATION_REQUIRED",
]


def test_v001_exists() -> None:
    assert MIGRATION.exists()


def test_v001_creates_both_tables_in_owned_schema() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "integration_tracking.integration_operations" in sql
    assert "integration_tracking.integration_operation_events" in sql
    assert "CREATE SCHEMA IF NOT EXISTS integration_tracking" in sql


def test_v001_status_check_covers_state_machine() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for status in _STATUSES:
        assert f"'{status}'" in sql


def test_v001_append_only_event_constraints() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "FOREIGN KEY (operation_id)" in sql
    assert "ON DELETE RESTRICT" in sql
    assert "UNIQUE (operation_id, sequence_number)" in sql


def test_v001_identity_and_tracing_columns() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    for column in (
        "operation_id",
        "correlation_id",
        "request_id",
        "idempotency_key",
        "environment_key",
        "caller_app",
        "actor_subject",
        "protheus_user_id",
        "request_payload",
        "outbound_payload",
        "response_payload",
        "request_hash",
        "outbound_hash",
        "confirmation_evidence",
        "attempt_count",
        "version",
        "send_started_at",
        "acknowledged_at",
        "confirmed_at",
    ):
        assert column in sql, column


def test_v001_no_destructive_ddl_and_no_secrets() -> None:
    sql = MIGRATION.read_text(encoding="utf-8").lower()
    assert "drop table" not in sql
    assert "drop schema" not in sql
    assert "truncate" not in sql
    assert "password" not in sql
    assert "psw_protheus" not in sql


def test_v001_useful_indexes() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")
    assert "(status)" in sql
    assert "(caller_app, actor_subject)" in sql
    assert "(integration, resource, action)" in sql
    assert "(correlation_id)" in sql
