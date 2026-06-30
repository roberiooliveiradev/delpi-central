from __future__ import annotations

from unittest.mock import MagicMock

from app.infrastructure.persistence.totvs.product_repositories.product_repository import (
    ProductRepository,
)


def test_search_products_filters_by_customer_reference() -> None:
    repo = ProductRepository()
    repo.execute_one = MagicMock(return_value={"total": 0})
    repo.execute_query = MagicMock(return_value=[])
    repo.__enter__ = MagicMock(return_value=repo)
    repo.__exit__ = MagicMock(return_value=False)

    repo.search_products(customer_reference="10018137", page=1, page_size=10)

    count_sql = repo.execute_one.call_args[0][0]
    data_sql = repo.execute_query.call_args[0][0]
    count_params = repo.execute_one.call_args[0][1]
    data_params = repo.execute_query.call_args[0][1]

    assert "B1_REFEREN" in count_sql
    assert "B1_REFEREN" in data_sql
    assert "10018137%" in count_params
    assert "10018137%" in data_params
