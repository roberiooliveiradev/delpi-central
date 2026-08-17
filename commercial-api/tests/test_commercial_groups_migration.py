from pathlib import Path

import pytest


V010 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "V010__commercial_groups.sql"
).read_text(encoding="utf-8")

V011 = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "V011__remove_default_commercial_groups.sql"
).read_text(encoding="utf-8")

LEGACY_SEED_KINDS = (
    "sellers",
    "sales_assistants",
    "billing",
    "estimators",
)


def test_v010_creates_groups_and_members_tables() -> None:
    assert "CREATE TABLE IF NOT EXISTS commercial.commercial_groups" in V010
    assert "CREATE TABLE IF NOT EXISTS commercial.commercial_group_members" in V010
    assert "UNIQUE (group_id, user_id)" in V010
    assert "REFERENCES commercial.commercial_groups (id) ON DELETE CASCADE" in V010


def test_v010_historically_seeded_kinds_for_compat() -> None:
    """V010 imutável ainda contém o INSERT legado; V011 remove os seeds."""
    for kind in LEGACY_SEED_KINDS:
        assert f"('{kind}'," in V010
    assert "ON CONFLICT (kind) DO NOTHING" in V010


def test_v011_removes_default_seed_groups() -> None:
    assert "DELETE FROM commercial.commercial_groups" in V011
    for kind in LEGACY_SEED_KINDS:
        assert f"'{kind}'" in V011


@pytest.mark.parametrize("kind", list(LEGACY_SEED_KINDS))
def test_migration_kind_is_english_identifier(kind: str) -> None:
    assert kind.isascii()
    assert kind.replace("_", "").isalpha() or kind.replace("_", "").isalnum()
    assert kind == kind.lower()
