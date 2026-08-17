"""Structural checks for recently-closed TOTVS SQL (post-audit)."""

from pathlib import Path


def test_recently_closed_sql_lookback_uses_datfat_not_emissao() -> None:
    src = Path(
        "app/infrastructure/persistence/totvs/pedidos_venda_abertos/"
        "recently_closed_orders_query_repository.py"
    ).read_text(encoding="utf-8")
    assert "C6_DATFAT" in src
    assert "DATEADD(DAY, -?, CAST(GETDATE() AS DATE))" in src or "DATEADD(DAY, -?" in src
    # Emission lookback was the wrong window for "recently closed".
    assert "C5_EMISSAO >=" not in src
    assert "C6_ENTREG" in src  # still selected as promised delivery display


def test_audit_script_exists() -> None:
    path = Path("scripts/sql/recently_closed_orders_audit.py")
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "C6_DATFAT" in text
    assert "current_api_filter_emissao_30d" in text
