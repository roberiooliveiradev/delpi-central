from pathlib import Path

from app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    SCHEMA_NAME,
    list_migration_files,
    parse_version_and_name,
)


def test_migrations_dir_and_v001_exist():
    assert MIGRATIONS_DIR.exists()
    files = list_migration_files()
    versions = [parse_version_and_name(path)[0] for path in files]
    assert "V001" in versions
    assert SCHEMA_NAME == "supplies"


def test_v001_sql_defines_preferences_uuid_pk():
    sql = (Path(MIGRATIONS_DIR) / "V001__create_supplies_schema.sql").read_text(
        encoding="utf-8"
    )
    assert "supply_user_preferences" in sql
    assert "user_id UUID PRIMARY KEY" in sql
    assert "keycloak_sub TEXT" in sql
