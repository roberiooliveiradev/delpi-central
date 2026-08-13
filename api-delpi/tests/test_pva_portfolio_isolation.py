"""PVA não acopla ao schema commercial (Portal)."""

from pathlib import Path


COMPOSER = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "composition"
    / "pedidos_venda_abertos_composer.py"
).read_text(encoding="utf-8")


def test_pva_composer_uses_only_legacy_seller_portfolio_repo() -> None:
    assert "PostgresSellerPortfolioRepository" in COMPOSER
    assert "DualReadSellerPortfolioRepository" not in COMPOSER
    assert "PostgresCommercialSellerPortfolioRepository" not in COMPOSER
    assert "commercial.seller_portfolios" not in COMPOSER
    assert "COMMERCIAL_PORTFOLIO_SOURCE" not in COMPOSER


def test_pva_seller_portfolio_sql_stays_in_pva_schema() -> None:
    repo = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "infrastructure"
        / "persistence"
        / "plugins"
        / "repositories"
        / "pedidos_venda_abertos"
        / "postgres_seller_portfolio_repository.py"
    ).read_text(encoding="utf-8")
    assert "pedidos_venda_abertos.sellers" in repo
    assert "commercial.seller_portfolios" not in repo
