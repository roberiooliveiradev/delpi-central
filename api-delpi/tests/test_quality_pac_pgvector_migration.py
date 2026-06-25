from __future__ import annotations

from pathlib import Path


def test_v011_pgvector_migration_declares_search_embedding():
    migration = (
        Path(__file__).resolve().parents[1]
        / "migrations"
        / "plugins"
        / "quality-action-plans"
        / "V011__pac_case_similarity_pgvector.sql"
    )

    sql = migration.read_text(encoding="utf-8")

    assert "CREATE EXTENSION IF NOT EXISTS vector" in sql
    assert "search_embedding vector(1024)" in sql
    assert "vector_cosine_ops" in sql
