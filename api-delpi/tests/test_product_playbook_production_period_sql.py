import inspect

from app.infrastructure.persistence.totvs.product_repositories import (
    product_playbook_repository,
)
from app.infrastructure.persistence.totvs.product_repositories.product_playbook_production_period_sql import (
    PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL,
)


def test_production_order_period_filter_sql_clauses() -> None:
    sql = PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL

    assert "H6P.H6_DTAPONT >= @DATA_INI" in sql
    assert "H6P.H6_DTAPONT < @DATA_FIM" in sql
    assert "C2_DATPRI < @DATA_FIM" in sql
    assert "C2_DATPRF >= @DATA_INI" in sql
    assert "C2_QUJE" in sql
    assert "C2_QUANT" in sql


def test_repository_wires_period_filter_and_date_params() -> None:
    source = inspect.getsource(product_playbook_repository.ProductPlaybookRepository)

    assert "PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL" in source
    assert "DECLARE @DATA_INI VARCHAR(8)" in source
    assert "DECLARE @DATA_FIM VARCHAR(8)" in source
    assert "date_start" in source
    assert "date_end_exclusive" in source
