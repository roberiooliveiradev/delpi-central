"""Numeração diária contra PostgreSQL real.

Só roda em banco local chamado plugins_number_test. Não aponta para produção.
"""

from __future__ import annotations

import os
import threading
import time
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from psycopg.errors import CheckViolation
from psycopg.rows import dict_row

from app.domain.engineering.metallographic_report import (
    ReportNumberCapacityError,
    business_calendar_date,
    format_report_number,
    normalize_create_payload,
    request_hash,
)
from app.infrastructure.pdf.metallographic.metallographic_report_pdf_renderer import (
    MetallographicReportPdfRenderer,
)
from app.infrastructure.persistence.plugins.repositories.engineering.postgres_metallographic_report_repository import (
    PostgresMetallographicReportRepository,
)

_REQUIRED = (
    "PLUGINS_DB_HOST",
    "PLUGINS_DB_PORT",
    "PLUGINS_DB_NAME",
    "PLUGINS_DB_USER",
    "PLUGINS_DB_PASSWORD",
)


def _local_test_database() -> bool:
    host = os.getenv("PLUGINS_DB_HOST", "").strip()
    name = os.getenv("PLUGINS_DB_NAME", "").strip()
    return host in {"127.0.0.1", "localhost"} and name == "plugins_number_test" and all(
        os.getenv(item, "").strip() for item in _REQUIRED
    )


pytestmark = pytest.mark.skipif(
    not _local_test_database(),
    reason="Exige PostgreSQL local plugins_number_test; não usa o banco de produção.",
)


def _connect():
    import psycopg

    from scripts.run_plugins_migrations import get_plugins_db_settings

    settings = get_plugins_db_settings()
    return psycopg.connect(conninfo=settings.dsn, row_factory=dict_row, autocommit=False)


def _reset_and_apply(conn, *, through: str) -> None:
    from scripts.run_plugins_migrations import (
        apply_migration,
        ensure_migrations_table,
        list_migration_files,
        parse_version_and_name,
    )

    with conn.cursor() as cursor:
        cursor.execute("DROP SCHEMA IF EXISTS engineering CASCADE")
    conn.commit()
    ensure_migrations_table(conn, "engineering")
    for path in list_migration_files("engineering"):
        version, _name = parse_version_and_name(path)
        if version > through:
            break
        apply_migration(conn, "engineering", path)


def _payload(**overrides):
    body = normalize_create_payload({"status": "draft", "report_date": "2020-01-15"})
    body.update(overrides)
    return body


def _create(repository, key: str, **overrides):
    payload = _payload(**overrides)
    return repository.create_report(
        actor="user-1",
        payload=payload,
        idempotency_key=key,
        request_hash=request_hash(payload),
    )


@pytest.fixture
def database():
    connection = _connect()
    _reset_and_apply(connection, through="V010")
    try:
        yield connection
    finally:
        connection.close()


def test_business_date_function_matches_sao_paulo_boundary(database) -> None:
    from scripts.run_plugins_migrations import apply_migration, list_migration_files

    apply_migration(
        database,
        "engineering",
        next(path for path in list_migration_files("engineering") if path.name.startswith("V011__")),
    )
    with database.cursor() as cursor:
        cursor.execute(
            """
            SELECT engineering.metallographic_business_date(%s) AS business_date
            """,
            (datetime(2026, 10, 22, 2, 30, tzinfo=timezone.utc),),
        )
        before = cursor.fetchone()["business_date"]
        cursor.execute(
            """
            SELECT engineering.metallographic_business_date(%s) AS business_date
            """,
            (datetime(2026, 10, 22, 3, 30, tzinfo=timezone.utc),),
        )
        after = cursor.fetchone()["business_date"]
    assert before.isoformat() == "2026-10-21"
    assert after.isoformat() == "2026-10-22"
    assert business_calendar_date(datetime(2026, 10, 22, 2, 30, tzinfo=timezone.utc)).isoformat() == "2026-10-21"
    assert business_calendar_date(datetime(2026, 10, 22, 3, 30, tzinfo=timezone.utc)).isoformat() == "2026-10-22"


def test_migration_renumbers_deleted_rows_and_keeps_relationships(database) -> None:
    deleted_id = "11111111-1111-4111-8111-111111111111"
    edited_date_id = "22222222-2222-4222-8222-222222222222"
    with_image_id = "33333333-3333-4333-8333-333333333333"
    tie_low = "44444444-4444-4444-8444-444444444441"
    tie_high = "44444444-4444-4444-8444-444444444442"
    with database.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO engineering.metallographic_reports (
                id, report_number, report_date, created_by, updated_by, created_at, deleted_at, deleted_by
            ) VALUES
                (%s, 'MET-2026-000001', NULL, 'tester', 'tester', %s, NOW(), 'tester'),
                (%s, 'MET-2026-000099', '2020-01-15', 'tester', 'tester', %s, NULL, NULL),
                (%s, 'MET-2026-000002', NULL, 'tester', 'tester', %s, NULL, NULL),
                (%s, 'MET-2026-000050', NULL, 'tester', 'tester', %s, NULL, NULL),
                (%s, 'MET-2026-000051', NULL, 'tester', 'tester', %s, NULL, NULL)
            """,
            (
                deleted_id,
                datetime(2026, 10, 22, 2, 30, tzinfo=timezone.utc),
                edited_date_id,
                datetime(2026, 10, 22, 3, 30, tzinfo=timezone.utc),
                with_image_id,
                datetime(2026, 10, 22, 4, 0, tzinfo=timezone.utc),
                tie_low,
                datetime(2026, 10, 22, 5, 0, tzinfo=timezone.utc),
                tie_high,
                datetime(2026, 10, 22, 5, 0, tzinfo=timezone.utc),
            ),
        )
        cursor.execute(
            """
            INSERT INTO engineering.metallographic_report_images (
                report_id, slot, content_type, size_bytes, sha256, stored_name, width, height
            ) VALUES (%s, 'original', 'image/png', 12, %s, 'original.png', 8, 8)
            """,
            (with_image_id, "a" * 64),
        )
        cursor.execute(
            """
            INSERT INTO engineering.metallographic_report_idempotency (
                actor_subject, operation, idempotency_key, request_hash, report_id
            ) VALUES ('tester', 'create', 'legacy-key-01', %s, %s)
            """,
            ("b" * 64, edited_date_id),
        )
    database.commit()

    from scripts.run_plugins_migrations import apply_migration, list_migration_files

    apply_migration(
        database,
        "engineering",
        next(path for path in list_migration_files("engineering") if path.name.startswith("V011__")),
    )

    with database.cursor() as cursor:
        cursor.execute(
            """
            SELECT id::text AS id, report_number, report_date::text AS report_date, deleted_at IS NOT NULL AS deleted
              FROM engineering.metallographic_reports
             ORDER BY created_at, id
            """
        )
        rows = cursor.fetchall()
        cursor.execute(
            "SELECT report_id::text AS report_id FROM engineering.metallographic_report_images"
        )
        images = cursor.fetchall()
        cursor.execute(
            """
            SELECT report_id::text AS report_id, previous_number, report_number
              FROM engineering.metallographic_report_number_renames
            """
        )
        renames = {row["report_id"]: row for row in cursor.fetchall()}
        cursor.execute(
            """
            SELECT business_date::text AS business_date, last_value
              FROM engineering.metallographic_report_day_counters
             ORDER BY business_date
            """
        )
        counters = cursor.fetchall()

    numbers = [row["report_number"] for row in rows]
    assert numbers == [
        "MET-20261021-001",
        "MET-20261022-001",
        "MET-20261022-002",
        "MET-20261022-003",
        "MET-20261022-004",
    ]
    assert rows[0]["id"] == deleted_id and rows[0]["deleted"] is True
    edited = next(row for row in rows if row["id"] == edited_date_id)
    assert edited["report_date"] == "2020-01-15"
    assert edited["report_number"] == "MET-20261022-001"
    assert images == [{"report_id": with_image_id}]
    assert renames[deleted_id]["previous_number"] == "MET-2026-000001"
    assert renames[deleted_id]["report_number"] == "MET-20261021-001"
    assert renames[edited_date_id]["previous_number"] == "MET-2026-000099"
    assert counters == [
        {"business_date": "2026-10-21", "last_value": 1},
        {"business_date": "2026-10-22", "last_value": 4},
    ]
    assert tie_low < tie_high
    assert numbers[3:].index("MET-20261022-003") == 0


def test_migration_aborts_when_a_day_exceeds_999(database) -> None:
    from scripts.run_plugins_migrations import MigrationError, apply_migration, list_migration_files

    with database.cursor() as cursor:
        cursor.executemany(
            """
            INSERT INTO engineering.metallographic_reports (
                report_number, created_by, updated_by, created_at
            ) VALUES (%s, 'tester', 'tester', %s)
            """,
            [
                (f"MET-2026-{index:06d}", datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc))
                for index in range(1, 1001)
            ],
        )
    database.commit()
    with pytest.raises(MigrationError, match="exceeds 999"):
        apply_migration(
            database,
            "engineering",
            next(path for path in list_migration_files("engineering") if path.name.startswith("V011__")),
        )
    with database.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM engineering.metallographic_reports")
        assert cursor.fetchone()["total"] == 1000
        cursor.execute(
            """
            SELECT COUNT(*) AS total
              FROM engineering.metallographic_reports
             WHERE report_number LIKE 'MET-20261022-%'
            """
        )
        assert cursor.fetchone()["total"] == 0
        cursor.execute(
            """
            SELECT 1
              FROM engineering.schema_migrations
             WHERE version = 'V011'
            """
        )
        assert cursor.fetchone() is None


def test_create_is_daily_immutable_and_transactional(database) -> None:
    from scripts.run_plugins_migrations import apply_migration, list_migration_files

    apply_migration(
        database,
        "engineering",
        next(path for path in list_migration_files("engineering") if path.name.startswith("V011__")),
    )
    repository = PostgresMetallographicReportRepository(database)
    first = _create(repository, "create-key-01")
    second = _create(repository, "create-key-02")
    with database.cursor() as cursor:
        cursor.execute("SELECT engineering.metallographic_business_date(NOW()) AS business_date")
        today = cursor.fetchone()["business_date"]
    assert first["public"]["report_number"] == format_report_number(today, 1)
    assert second["public"]["report_number"] == format_report_number(today, 2)

    replay = _create(repository, "create-key-01")
    assert replay["public"]["id"] == first["public"]["id"]
    assert replay["public"]["report_number"] == first["public"]["report_number"]
    with database.cursor() as cursor:
        cursor.execute(
            "SELECT last_value FROM engineering.metallographic_report_day_counters WHERE business_date = %s",
            (today,),
        )
        assert cursor.fetchone()["last_value"] == 2

    updated = repository.update_report(
        actor="user-2",
        report_id=first["public"]["id"],
        expected_version=1,
        changes={"report_date": "1999-12-31"},
    )
    assert updated["public"]["report_date"] == "1999-12-31"
    assert updated["public"]["report_number"] == first["public"]["report_number"]

    copied = repository.copy_report(
        actor="user-2",
        source_id=first["public"]["id"],
        report_id=str(uuid4()),
        payload=_payload(),
        idempotency_key="copy-key-0001",
        request_hash=request_hash(_payload()),
        images=[],
    )
    assert copied["public"]["id"] != first["public"]["id"]
    assert copied["public"]["report_number"] == format_report_number(today, 3)

    repository.soft_delete(
        actor="user-1",
        report_id=second["public"]["id"],
        expected_version=1,
    )
    after_delete = _create(repository, "create-key-03")
    assert after_delete["public"]["report_number"] == format_report_number(today, 4)
    with database.cursor() as cursor:
        cursor.execute(
            "SELECT report_number FROM engineering.metallographic_reports WHERE id = %s",
            (second["public"]["id"],),
        )
        assert cursor.fetchone()["report_number"] == format_report_number(today, 2)

    listed = repository.list_reports(
        filters={"report_number": format_report_number(today, 1)},
        page=1,
        page_size=20,
        sort="report_number_asc",
    )
    assert [item["report_number"] for item in listed["items"]] == [format_report_number(today, 1)]
    pdf = MetallographicReportPdfRenderer().render(first["public"], {})
    assert first["public"]["report_number"].encode("latin1") in pdf
    assert b"RASCUNHO" not in pdf

    broken = _payload()
    broken["status"] = "published"
    before = listed["total"]
    with pytest.raises(CheckViolation):
        repository.create_report(
            actor="user-1",
            payload=broken,
            idempotency_key="create-key-broken",
            request_hash=request_hash(broken),
        )
    database.rollback()
    with database.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM engineering.metallographic_reports WHERE deleted_at IS NULL")
        assert cursor.fetchone()["total"] == 3
        cursor.execute(
            "SELECT last_value FROM engineering.metallographic_report_day_counters WHERE business_date = %s",
            (today,),
        )
        assert cursor.fetchone()["last_value"] == 4

    with database.cursor() as cursor:
        cursor.execute(
            """
            UPDATE engineering.metallographic_report_day_counters
               SET last_value = 999
             WHERE business_date = %s
            """,
            (today,),
        )
    database.commit()
    with pytest.raises(ReportNumberCapacityError):
        _create(repository, "create-key-full")
    database.rollback()
    with database.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM engineering.metallographic_reports")
        assert cursor.fetchone()["total"] == 4
        cursor.execute(
            "SELECT last_value FROM engineering.metallographic_report_day_counters WHERE business_date = %s",
            (today,),
        )
        assert cursor.fetchone()["last_value"] == 999
    assert before >= 1


def test_concurrent_creates_do_not_share_a_number(database) -> None:
    from scripts.run_plugins_migrations import apply_migration, list_migration_files

    apply_migration(
        database,
        "engineering",
        next(path for path in list_migration_files("engineering") if path.name.startswith("V011__")),
    )
    database.commit()
    results: dict[int, str] = {}
    errors: dict[int, BaseException] = {}

    def _worker(index: int) -> None:
        connection = _connect()
        try:
            repository = PostgresMetallographicReportRepository(connection)
            payload = _payload()
            stored = repository.create_report(
                actor="user-1",
                payload=payload,
                idempotency_key=f"race-key-{index:02d}",
                request_hash=request_hash(payload),
            )
            results[index] = stored["public"]["report_number"]
        except BaseException as exc:
            errors[index] = exc
            connection.rollback()
        finally:
            connection.close()

    threads = [threading.Thread(target=_worker, args=(index,)) for index in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)
    assert errors == {}
    assert len(set(results.values())) == 2
    assert {value[-3:] for value in results.values()} == {"001", "002"}


def test_rolled_back_reservation_is_issued_again(database) -> None:
    from scripts.run_plugins_migrations import apply_migration, list_migration_files

    apply_migration(
        database,
        "engineering",
        next(path for path in list_migration_files("engineering") if path.name.startswith("V011__")),
    )
    with database.cursor() as cursor:
        cursor.execute("SELECT engineering.metallographic_business_date(NOW()) AS business_date")
        today = cursor.fetchone()["business_date"]
        cursor.execute("SET lock_timeout = '5s'")
        cursor.execute(
            """
            INSERT INTO engineering.metallographic_report_day_counters (business_date, last_value)
            VALUES (%s, 1)
            """,
            (today,),
        )
    outcome: dict[str, str] = {}
    failure: dict[str, BaseException] = {}

    def _blocked() -> None:
        connection = _connect()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout = '5s'")
            repository = PostgresMetallographicReportRepository(connection)
            stored = _create(repository, "rollback-key-01")
            outcome["number"] = stored["public"]["report_number"]
        except BaseException as exc:
            failure["error"] = exc
            connection.rollback()
        finally:
            connection.close()

    worker = threading.Thread(target=_blocked)
    worker.start()
    waiting = False
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with database.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                  FROM pg_stat_activity
                 WHERE datname = current_database()
                   AND wait_event_type = 'Lock'
                   AND pid <> pg_backend_pid()
                """
            )
            if int(cursor.fetchone()["total"]) >= 1:
                waiting = True
                break
        time.sleep(0.05)
    assert waiting, "a segunda criação não esperou o lock da sequência"
    database.rollback()
    worker.join(timeout=5)
    assert failure == {}
    assert outcome["number"] == format_report_number(today, 1)
    with database.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) AS total FROM engineering.metallographic_reports")
        assert cursor.fetchone()["total"] == 1
        cursor.execute(
            "SELECT last_value FROM engineering.metallographic_report_day_counters WHERE business_date = %s",
            (today,),
        )
        assert cursor.fetchone()["last_value"] == 1
