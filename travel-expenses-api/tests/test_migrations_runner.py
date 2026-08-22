from travel_expenses_app.infrastructure.persistence.migrations_runner import (
    MIGRATIONS_DIR,
    calculate_checksum,
    list_migration_files,
    parse_version_and_name,
)


def test_v001_is_present_and_parseable():
    files = list_migration_files()
    names = [path.name for path in files]
    assert "V001__create_travel_expenses.sql" in names
    version, name = parse_version_and_name(files[0])
    assert version.startswith("V")
    assert name
    checksum = calculate_checksum(MIGRATIONS_DIR / "V001__create_travel_expenses.sql")
    assert len(checksum) == 64
