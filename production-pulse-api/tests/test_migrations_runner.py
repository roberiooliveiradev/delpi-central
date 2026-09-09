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


def test_v010_firmware_ota_is_present_and_parseable():
    migrations = _discover_migrations()
    by_version = {m.version: m for m in migrations}
    assert 10 in by_version
    assert by_version[10].name == "firmware_ota"
    path = _migrations_dir() / "V010__firmware_ota.sql"
    text = path.read_text(encoding="utf-8")
    assert "production_pulse.firmwares" in text
    assert "production_pulse.firmware_update_jobs" in text
    assert "production_pulse.firmware_update_targets" in text
    assert "installed_firmware_version" in text
    assert len(_checksum(text)) == 64


def test_v011_firmware_ota_progress_is_present_and_parseable():
    migrations = _discover_migrations()
    by_version = {m.version: m for m in migrations}
    assert 11 in by_version
    assert by_version[11].name == "firmware_ota_progress"
    path = _migrations_dir() / "V011__firmware_ota_progress.sql"
    text = path.read_text(encoding="utf-8")
    assert "bytes_received" in text
    assert "bytes_total" in text
    assert "progress_percent" in text
    assert len(_checksum(text)) == 64


def test_v012_firmware_archive_is_present_and_parseable():
    migrations = _discover_migrations()
    by_version = {m.version: m for m in migrations}
    assert 12 in by_version
    assert by_version[12].name == "firmware_archive"
    path = _migrations_dir() / "V012__firmware_archive.sql"
    text = path.read_text(encoding="utf-8")
    assert "archived_at" in text
    assert len(_checksum(text)) == 64


def test_v013_firmware_version_source_draft_is_present_and_parseable():
    migrations = _discover_migrations()
    by_version = {m.version: m for m in migrations}
    assert 13 in by_version
    assert by_version[13].name == "firmware_version_source_draft"
    path = _migrations_dir() / "V013__firmware_version_source_draft.sql"
    text = path.read_text(encoding="utf-8")
    assert "source_text" in text
    assert "firmwares_published_requires_artifact" in text
    assert len(_checksum(text)) == 64
