from pathlib import Path

import pytest

from commercial_app.domain.services.commercial_groups_messages_content_service import (
    CommercialGroupsMessagesContentService,
)


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "V010__commercial_groups.sql"
).read_text(encoding="utf-8")

EXPECTED_SEED = {
    "sellers": "Vendedores",
    "sales_assistants": "Auxiliares de vendas",
    "billing": "Faturamento",
    "estimators": "Orçamentistas",
}


def test_v010_creates_groups_and_members_tables() -> None:
    assert "CREATE TABLE IF NOT EXISTS commercial.commercial_groups" in MIGRATION
    assert "CREATE TABLE IF NOT EXISTS commercial.commercial_group_members" in MIGRATION
    assert "UNIQUE (group_id, user_id)" in MIGRATION
    assert "REFERENCES commercial.commercial_groups (id) ON DELETE CASCADE" in MIGRATION


def test_v010_seeds_four_operational_kinds() -> None:
    for kind, name in EXPECTED_SEED.items():
        assert f"('{kind}', '{name}'" in MIGRATION or f"('{kind}', '{name}'," in MIGRATION
    assert "ON CONFLICT (kind) DO NOTHING" in MIGRATION
    # Exactly four seed rows in the VALUES block.
    assert MIGRATION.count("', '") >= 4


def test_seed_kinds_content_matches_migration() -> None:
    content_seeds = CommercialGroupsMessagesContentService.seed_kinds()
    assert content_seeds == EXPECTED_SEED


@pytest.mark.parametrize("kind", list(EXPECTED_SEED))
def test_migration_kind_is_english_identifier(kind: str) -> None:
    assert kind.isascii()
    assert kind.replace("_", "").isalpha() or kind.replace("_", "").isalnum()
    assert kind == kind.lower()
