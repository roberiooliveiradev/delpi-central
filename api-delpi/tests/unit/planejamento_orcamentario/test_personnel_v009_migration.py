"""Migration V009 — cargo livre no Orçamento de Pessoal (Fase 3B.1.1).

Upgrade: run_plugins_migrations up --plugin planejamento-orcamentario
Não usar reset em ambientes com dados.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

PLUGIN_SLUG = "planejamento-orcamentario"
SCHEMA = "planejamento_orcamentario"
MIGRATIONS_DIR = (
    Path(__file__).resolve().parents[3]
    / "migrations"
    / "plugins"
    / PLUGIN_SLUG
)
MIGRATION_V008 = MIGRATIONS_DIR / "V008__create_personnel_budget_base.sql"
MIGRATION_V009 = (
    MIGRATIONS_DIR / "V009__replace_personnel_position_catalog_with_free_text.sql"
)


def _plugins_env_ready() -> bool:
    return all(
        os.getenv(name, "").strip()
        for name in (
            "PLUGINS_DB_HOST",
            "PLUGINS_DB_PORT",
            "PLUGINS_DB_NAME",
            "PLUGINS_DB_USER",
            "PLUGINS_DB_PASSWORD",
        )
    )


pytestmark_live = pytest.mark.skipif(
    not _plugins_env_ready(),
    reason="PLUGINS_DB_* ausente — testes live de migration ignorados",
)


def test_v009_migration_file_replaces_catalog_with_position_name() -> None:
    assert MIGRATION_V009.is_file()
    sql = MIGRATION_V009.read_text(encoding="utf-8")
    assert "position_name VARCHAR(200)" in sql
    assert "FROM planejamento_orcamentario.personnel_positions" in sql
    assert "l.position_id = p.id" in sql
    assert "V009 bloqueada" in sql
    assert "DROP COLUMN IF EXISTS position_id" in sql
    assert "DROP TABLE IF EXISTS planejamento_orcamentario.personnel_positions" in sql
    assert "uq_po_personnel_plan_line_active_position_name" in sql
    assert "lower(BTRIM(position_name))" in sql
    assert "ck_po_personnel_line_position_name" in sql
    # V008 permanece imutável e ainda declara o catálogo histórico
    v008 = MIGRATION_V008.read_text(encoding="utf-8")
    assert "personnel_positions" in v008
    assert "position_id" in v008


@pytestmark_live
def test_v009_applied_schema_has_position_name_without_catalog() -> None:
    from scripts.run_plugins_migrations import get_connection, run_plugin_migrations

    run_plugin_migrations(PLUGIN_SLUG)
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT version, checksum IS NOT NULL AS has_checksum
                FROM "{SCHEMA}".schema_migrations
                WHERE version = 'V009'
                """
            )
            row = cur.fetchone()
            assert row is not None, "V009 deve estar aplicada"

            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables
                    WHERE table_schema = %s AND table_name = 'personnel_positions'
                ) AS exists
                """,
                (SCHEMA,),
            )
            assert cur.fetchone()["exists"] is False

            cur.execute(
                """
                SELECT column_name, data_type, character_maximum_length, is_nullable
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = 'personnel_plan_lines'
                  AND column_name IN ('position_name', 'position_id')
                ORDER BY column_name
                """,
                (SCHEMA,),
            )
            cols = {r["column_name"]: r for r in cur.fetchall()}
            assert "position_id" not in cols
            assert "position_name" in cols
            assert cols["position_name"]["character_maximum_length"] == 200
            assert cols["position_name"]["is_nullable"] == "NO"

            cur.execute(
                """
                SELECT indexname FROM pg_indexes
                WHERE schemaname = %s
                  AND indexname = 'uq_po_personnel_plan_line_active_position_name'
                """,
                (SCHEMA,),
            )
            assert cur.fetchone() is not None


@pytestmark_live
def test_v009_backfill_logic_preserves_position_name_from_catalog() -> None:
    """Simula linha V008 (position_id) → position_name sem tocar o schema do plugin."""
    from scripts.run_plugins_migrations import get_connection

    with get_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("CREATE SCHEMA IF NOT EXISTS po_v009_sandbox")
                cur.execute("DROP TABLE IF EXISTS po_v009_sandbox.lines CASCADE")
                cur.execute("DROP TABLE IF EXISTS po_v009_sandbox.positions CASCADE")
                cur.execute(
                    """
                    CREATE TABLE po_v009_sandbox.positions (
                        id UUID PRIMARY KEY,
                        name VARCHAR(200) NOT NULL
                    )
                    """
                )
                cur.execute(
                    """
                    CREATE TABLE po_v009_sandbox.lines (
                        id UUID PRIMARY KEY,
                        position_id UUID NOT NULL
                            REFERENCES po_v009_sandbox.positions(id),
                        position_name VARCHAR(200)
                    )
                    """
                )
                cur.execute(
                    """
                    INSERT INTO po_v009_sandbox.positions (id, name)
                    VALUES
                      ('11111111-1111-1111-1111-111111111111', '  Operador de Produção  '),
                      ('22222222-2222-2222-2222-222222222222', 'Analista de Qualidade')
                    """
                )
                cur.execute(
                    """
                    INSERT INTO po_v009_sandbox.lines (id, position_id)
                    VALUES
                      ('aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
                       '11111111-1111-1111-1111-111111111111'),
                      ('bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
                       '22222222-2222-2222-2222-222222222222')
                    """
                )
                # Mesma lógica da V009 (backfill + guard + drop FK/coluna/catálogo)
                cur.execute(
                    """
                    UPDATE po_v009_sandbox.lines AS l
                    SET position_name = BTRIM(p.name)
                    FROM po_v009_sandbox.positions AS p
                    WHERE l.position_id = p.id
                      AND (l.position_name IS NULL OR BTRIM(l.position_name) = '')
                    """
                )
                cur.execute(
                    """
                    SELECT COUNT(*) AS missing
                    FROM po_v009_sandbox.lines
                    WHERE position_name IS NULL OR BTRIM(position_name) = ''
                    """
                )
                assert cur.fetchone()["missing"] == 0
                cur.execute(
                    """
                    ALTER TABLE po_v009_sandbox.lines
                        ALTER COLUMN position_name SET NOT NULL,
                        DROP COLUMN position_id
                    """
                )
                cur.execute("DROP TABLE po_v009_sandbox.positions")
                cur.execute(
                    """
                    SELECT id, position_name
                    FROM po_v009_sandbox.lines
                    ORDER BY position_name
                    """
                )
                rows = [
                    {
                        "id": str(r["id"]),
                        "position_name": r["position_name"],
                    }
                    for r in cur.fetchall()
                ]
                assert rows == [
                    {
                        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
                        "position_name": "Analista de Qualidade",
                    },
                    {
                        "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                        "position_name": "Operador de Produção",
                    },
                ]
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'po_v009_sandbox'
                          AND table_name = 'positions'
                    ) AS exists
                    """
                )
                assert cur.fetchone()["exists"] is False
        finally:
            conn.rollback()
