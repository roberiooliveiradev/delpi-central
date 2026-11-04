"""SQL SB1 identity — igualdade exata, sem LIKE/prefixo."""

from __future__ import annotations

from app.infrastructure.persistence.totvs.product_repositories.product_sb1_identity_lookup_sql import (
    lookup_by_codes_sql,
    lookup_by_customer_references_sql,
)


def test_lookup_by_codes_uses_exact_in_without_like() -> None:
    sql = lookup_by_codes_sql(3)
    assert "LIKE" not in sql.upper()
    assert "TOP 1" not in sql.upper()
    assert "B1_COD" in sql
    assert "B1_MSBLQL" in sql
    assert sql.count("?") == 3


def test_lookup_by_references_uses_exact_in_without_like() -> None:
    sql = lookup_by_customer_references_sql(2)
    assert "LIKE" not in sql.upper()
    assert "TOP 1" not in sql.upper()
    assert "B1_REFEREN" in sql
    assert sql.count("?") == 2
