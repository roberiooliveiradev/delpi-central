from app.application.dto.supplies.get_otd_request import GetOTDRequest
from app.infrastructure.persistence.totvs.supplies_repositories.otd_query_repository import (
    OtdQueryRepository,
)


def _repository() -> OtdQueryRepository:
    return OtdQueryRepository()


def test_monthly_breakdown_sql_uses_nolock_on_monthly_view() -> None:
    repo = _repository()
    request = GetOTDRequest(branch="01", start_date="20260401", end_date="20260430")

    where_clause, _ = repo._build_monthly_filters(request)
    sql = f"""
            SELECT
                FILIAL AS branch
            FROM VW_PONTUALIDADE_FORNECEDORES_MENSAL WITH (NOLOCK)
            WHERE {where_clause}
        """

    assert "WITH (NOLOCK)" in sql
    assert "VW_PONTUALIDADE_FORNECEDORES_MENSAL" in sql


def test_details_sql_uses_nolock_on_detail_view() -> None:
    repo = _repository()
    request = GetOTDRequest(branch="01", start_date="20260401", end_date="20260430")

    where_clause, _ = repo._build_details_filters(request)
    sql = f"""
            SELECT TOP 5
                FORNECEDOR AS supplier_code
            FROM VW_PONTUALIDADE_FORNECEDORES WITH (NOLOCK)
            WHERE {where_clause}
        """

    assert "WITH (NOLOCK)" in sql
    assert "VW_PONTUALIDADE_FORNECEDORES" in sql
