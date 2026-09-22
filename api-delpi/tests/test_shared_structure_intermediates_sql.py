"""SQL — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from app.domain.production.shared_structure_intermediates_scope import MAX_BOM_DEPTH
from app.infrastructure.persistence.totvs.production import (
    shared_structure_intermediates_sql as sql,
)


def test_active_pa_uses_sh6_productive_appointments_on_pa() -> None:
    query, params = sql.build_shared_intermediates_summary_query(
        branch="01",
        movement_from="20250901",
        movement_to_exclusive="20250922",
    )

    assert "#ACTIVE_PA" in query
    assert "H6_TIPO = 'P'" in query
    assert "H6_DTAPONT >= ?" in query
    assert "H6_DTAPONT < ?" in query
    assert "PA.B1_TIPO = 'PA'" in query
    assert "8000%" in query
    assert params == ("01", "20250901", "20250922", MAX_BOM_DEPTH)


def test_bom_uses_today_validity_and_pi_pa_components() -> None:
    query, _ = sql.build_shared_intermediates_summary_query(
        branch="01",
        movement_from="20250901",
        movement_to_exclusive="20250922",
    )

    assert "GETDATE()" in query
    assert "G1.G1_INI" in query
    assert "G1.G1_FIM" in query
    assert "B1_TIPO IN ('PI', 'PA')" in query
    assert "component_code <> BR.pa_code" in query


def test_shared_requires_two_or_more_pas() -> None:
    query, _ = sql.build_shared_intermediates_summary_query(
        branch="01",
        movement_from="20250901",
        movement_to_exclusive="20250922",
    )

    assert "#SHARED" in query
    assert "HAVING COUNT(DISTINCT pa_code) >= 2" in query
    assert "shared_intermediate_count" in query
    assert "checked_pa_count" in query


def test_page_query_paginates_intermediates() -> None:
    query, params = sql.build_shared_intermediates_query(
        offset=10,
        page_size=25,
        branch="02",
        movement_from="20250101",
        movement_to_exclusive="20250922",
    )

    assert "item_rank > ? AND item_rank <= ?" in query
    assert "finished_products" not in query
    assert "pa_code" in query
    assert params == ("02", "20250101", "20250922", MAX_BOM_DEPTH, 10, 35)


def test_temp_tables_are_dropped() -> None:
    query, _ = sql.build_shared_intermediates_query(
        offset=0,
        page_size=10,
        branch="01",
        movement_from="20250901",
        movement_to_exclusive="20250922",
    )

    for table in ("#ACTIVE_PA", "#PA_BOM", "#SHARED"):
        assert f"DROP TABLE IF EXISTS {table};" in query
