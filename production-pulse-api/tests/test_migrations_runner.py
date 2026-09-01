from production_pulse_app.infrastructure.persistence.migrations_runner import (
    MIGRATION_FILENAME_RE,
    _checksum,
    _discover_migrations,
    _migrations_dir,
)


def test_migrations_dir_exists():
    migrations_dir = _migrations_dir()
    assert migrations_dir.is_dir()


def test_v001_is_present_and_parseable():
    migrations = _discover_migrations()
    assert len(migrations) >= 1
    first = migrations[0]
    assert first.version == 1
    assert first.name == "create_production_pulse_schema"
    match = MIGRATION_FILENAME_RE.match(first.path.name)
    assert match is not None


def test_v001_checksum_is_sha256():
    path = _migrations_dir() / "V001__create_production_pulse_schema.sql"
    assert path.is_file()
    checksum = _checksum(path.read_text(encoding="utf-8"))
    assert len(checksum) == 64
