from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.domain.totvs.protheus_product_types import (
    PRODUCT_TYPE_RAW_MATERIAL,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX,
    SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN,
)
from app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository import (
    OtdQueryRepository,
)


def _repository() -> OtdQueryRepository:
    return OtdQueryRepository()


def test_product_universe_clause_is_mp_or_code_prefix() -> None:
    clause, params = OtdQueryRepository._product_universe_clause()
    assert "TIPO_PRODUTO" in clause
    assert " OR " in clause
    assert f"LEFT(RTRIM(LTRIM(PRODUTO)), {SUPPLIES_OTD_PRODUCT_CODE_PREFIX_LEN})" in clause
    assert params == (PRODUCT_TYPE_RAW_MATERIAL, SUPPLIES_OTD_PRODUCT_CODE_PREFIX)


def test_details_filters_include_product_universe_and_binds() -> None:
    repo = _repository()
    request = GetOTDRequest(branch="01", start_date="20260401", end_date="20260430")

    where_clause, params = repo._build_details_filters(request)

    assert "VW_PONTUALIDADE_FORNECEDORES" not in where_clause
    assert "TIPO_PRODUTO" in where_clause
    assert " OR " in where_clause
    assert PRODUCT_TYPE_RAW_MATERIAL in params
    assert SUPPLIES_OTD_PRODUCT_CODE_PREFIX in params
    assert "01" in params


def test_monthly_breakdown_sql_uses_detail_view_with_nolock_and_universe() -> None:
    repo = _repository()
    request = GetOTDRequest(branch="01", start_date="20260401", end_date="20260430")

    where_clause, params = repo._build_details_filters(request)
    sql = f"""
            SELECT
                FILIAL AS branch
            FROM VW_PONTUALIDADE_FORNECEDORES WITH (NOLOCK)
            WHERE {where_clause}
        """

    assert "WITH (NOLOCK)" in sql
    assert "VW_PONTUALIDADE_FORNECEDORES" in sql
    assert "VW_PONTUALIDADE_FORNECEDORES_MENSAL" not in sql
    assert "TIPO_PRODUTO" in sql
    assert PRODUCT_TYPE_RAW_MATERIAL in params
    assert SUPPLIES_OTD_PRODUCT_CODE_PREFIX in params


def test_details_sql_uses_nolock_on_detail_view() -> None:
    repo = _repository()
    request = GetOTDRequest(branch="01", start_date="20260401", end_date="20260430")

    where_clause, params = repo._build_details_filters(request)
    sql = f"""
            SELECT TOP 5
                FORNECEDOR AS supplier_code
            FROM VW_PONTUALIDADE_FORNECEDORES WITH (NOLOCK)
            WHERE {where_clause}
        """

    assert "WITH (NOLOCK)" in sql
    assert "VW_PONTUALIDADE_FORNECEDORES" in sql
    assert " OR " in where_clause
    assert SUPPLIES_OTD_PRODUCT_CODE_PREFIX in params
