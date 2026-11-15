from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.infrastructure.persistence.totvs.product_repositories.product_repository import (
    ProductRepository,
)


def _repo() -> ProductRepository:
    repo = ProductRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])
    return repo


def test_search_products_filters_by_previous_code_exact() -> None:
    repo = _repo()
    with patch.object(ProductRepository, "_connect"):
        repo.search_products(previous_code="80015472", page=1, page_size=10)

    count_sql = repo.execute_one.call_args[0][0]
    data_sql = repo.execute_query.call_args[0][0]
    count_params = repo.execute_one.call_args[0][1]
    data_params = repo.execute_query.call_args[0][1]

    assert "LTRIM(RTRIM(SB1.B1_CODANT)) = ?" in count_sql
    assert "LTRIM(RTRIM(SB1.B1_CODANT)) = ?" in data_sql
    assert "80015472" in count_params
    assert "80015472" in data_params


def test_search_products_previous_code_preserves_leading_zeros() -> None:
    repo = _repo()
    with patch.object(ProductRepository, "_connect"):
        repo.search_products(previous_code="00800154")

    params = repo.execute_query.call_args[0][1]
    assert "00800154" in params
    assert "800154" not in params


def test_search_products_previous_code_strips_outer_whitespace() -> None:
    repo = _repo()
    with patch.object(ProductRepository, "_connect"):
        repo.search_products(previous_code="  80015472  ")

    params = repo.execute_query.call_args[0][1]
    assert "80015472" in params
    assert "  80015472  " not in params


def test_search_products_without_previous_code_omits_clause() -> None:
    repo = _repo()
    with patch.object(ProductRepository, "_connect"):
        repo.search_products(code="FIO")

    sql = repo.execute_query.call_args[0][0]
    assert "LTRIM(RTRIM(SB1.B1_CODANT))" not in sql


def test_search_products_previous_code_combines_with_other_filters() -> None:
    repo = _repo()
    with patch.object(ProductRepository, "_connect"):
        repo.search_products(
            previous_code="80015472",
            group="9026",
            product_type=["PA"],
        )

    sql = repo.execute_query.call_args[0][0]
    params = repo.execute_query.call_args[0][1]
    assert "LTRIM(RTRIM(SB1.B1_CODANT)) = ?" in sql
    assert "SB1.B1_GRUPO = ?" in sql
    assert "SB1.B1_TIPO IN (?)" in sql
    assert "80015472" in params
    assert "9026" in params
    assert "PA" in params


def test_search_products_previous_code_is_parameterized() -> None:
    """Injection attempt must stay a bound param, never reach the SQL text."""
    repo = _repo()
    with patch.object(ProductRepository, "_connect"):
        repo.search_products(previous_code="80015472' OR '1'='1")

    sql = repo.execute_query.call_args[0][0]
    params = repo.execute_query.call_args[0][1]
    assert "' OR '1'='1" not in sql
    assert "80015472' OR '1'='1" in params
