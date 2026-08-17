from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "V013__seller_portfolio_user_id_nullable.sql"
).read_text(encoding="utf-8")


def test_v013_makes_seller_portfolio_user_id_nullable() -> None:
    assert "ALTER COLUMN user_id DROP NOT NULL" in MIGRATION
    assert "seller_portfolios" in MIGRATION
    # Imutabilidade: não reescreve V001.
    assert "DROP TABLE" not in MIGRATION
