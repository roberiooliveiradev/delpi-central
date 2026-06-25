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
    assert "SH8010" in sql
    assert "H8_DTINI >= @DATA_INI" in sql
    assert "H8_DTINI < @DATA_FIM" in sql
    assert "SD4010" in sql


def test_repository_wires_period_filter_and_date_params() -> None:
    source = inspect.getsource(product_playbook_repository.ProductPlaybookRepository)

    assert "PRODUCT_PLAYBOOK_PRODUCTION_ORDER_PERIOD_FILTER_SQL" in source
    assert "DECLARE @DATA_INI VARCHAR(8)" in source
    assert "DECLARE @DATA_FIM VARCHAR(8)" in source
    assert "date_start" in source
    assert "date_end_exclusive" in source


def test_structure_exclusivity_uses_forward_pa_bom_for_mp_usage() -> None:
    source = inspect.getsource(product_playbook_repository.ProductPlaybookRepository)

    assert "ESTRUTURA_PA AS" in source
    assert "MP_ANCESTORS AS" not in source
    assert "TODAS_ESTRUTURAS_VALIDAS" not in source


def test_production_status_scopes_apontamentos_to_bom_scope() -> None:
    source = inspect.getsource(
        product_playbook_repository.ProductPlaybookRepository.fetch_production_status
    )

    assert "FROM ESCOPO_PRODUCAO" in source
    assert "EP.product_code = H6.H6_PRODUTO" in source
    assert "FROM SH6010 WITH (NOLOCK)\n            WHERE D_E_L_E_T_" not in source


def test_raw_material_stock_scopes_sb2_to_bom_mps() -> None:
    source = inspect.getsource(
        product_playbook_repository.ProductPlaybookRepository.fetch_raw_material_stock
    )

    assert "INNER JOIN MPS MP" in source
    assert "ON MP.raw_material_code = B2.B2_COD" in source
