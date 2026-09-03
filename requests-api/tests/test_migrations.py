from requests_app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    SCHEMA_NAME,
    calculate_checksum,
    list_migration_files,
    parse_version_and_name,
)


def test_migrations_dir_exists():
    assert MIGRATIONS_DIR.is_dir()


def test_list_migration_files_in_order():
    files = list_migration_files()
    names = [path.name for path in files]
    assert names == [
        "V001__schema_migrations.sql",
        "V002__core_domain.sql",
        "V003__idempotency_keys.sql",
        "V004__attachments_artifacts_events.sql",
        "V005__integration_outbox.sql",
    ]


def test_parse_version_and_name():
    version, name = parse_version_and_name(list_migration_files()[0])
    assert version == "V001"
    assert name == "schema_migrations"


def test_calculate_checksum_is_stable():
    path = list_migration_files()[0]
    first = calculate_checksum(path)
    second = calculate_checksum(path)
    assert first == second
    assert len(first) == 64


def test_schema_name():
    assert SCHEMA_NAME == "my_requests"


def test_v002_contains_core_tables():
    v002 = MIGRATIONS_DIR / "V002__core_domain.sql"
    sql = v002.read_text(encoding="utf-8")
    for table in (
        "request_types",
        "requests",
        "request_status_history",
        "request_assignments",
        "request_comments",
    ):
        assert table in sql

    _, name = parse_version_and_name(v002)
    assert name == "core_domain"


def test_v003_idempotency_keys():
    v003 = MIGRATIONS_DIR / "V003__idempotency_keys.sql"
    sql = v003.read_text(encoding="utf-8")
    assert "idempotency_keys" in sql
    _, name = parse_version_and_name(v003)
    assert name == "idempotency_keys"
