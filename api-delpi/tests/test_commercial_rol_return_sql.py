from app.domain.services.commercial.commercial_rol_return_sql import (
    CommercialRolReturnSql,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from unittest.mock import patch


def test_sales_return_predicate_requires_duplic_for_tipo_d() -> None:
    predicate = CommercialRolReturnSql.sales_return_predicate(
        d1_alias="D1",
        f4_alias="F4D",
    )
    assert "D1.D1_CF IN ('1201', '2201')" in predicate
    assert "D1.D1_TIPO = 'D'" in predicate
    assert "F4D.F4_DUPLIC" in predicate
    assert "OR D1.D1_TIPO = 'D')" not in predicate.replace(" ", "")


def test_sale_eligibility_predicate_includes_tes_and_cf_rules() -> None:
    pred = CommercialRolReturnSql.sale_eligibility_predicate(
        exists_where="D1X.D1_DTDIGIT >= ? AND D1X.D1_DTDIGIT <= ?",
    )
    assert "F4_DUPLIC" in pred
    assert "5911" in pred
    assert "D1X.D1_DTDIGIT" in pred


def test_market_predicates_use_cfop_first_digit() -> None:
    domestic = CommercialRolReturnSql.is_domestic_market_predicate(d2_alias="D2")
    export = CommercialRolReturnSql.is_export_market_predicate(d2_alias="D2")
    assert "LEFT(LTRIM(RTRIM(ISNULL(D2.D2_CF, ''))), 1)" in domestic
    assert "'5'" in domestic and "'6'" in domestic
    assert "'7'" in export
    assert CommercialRolReturnSql.market_filter_predicate(None) is None
    assert CommercialRolReturnSql.market_filter_predicate("domestic") == domestic
    assert CommercialRolReturnSql.market_filter_predicate("export") == export


def test_market_filter_rejects_unknown() -> None:
    try:
        CommercialRolReturnSql.market_filter_predicate("weird")
        raise AssertionError("expected ValueError")
    except ValueError as exc:
        assert "market" in str(exc).lower()


def test_get_rol_sql_excludes_tipo_d_without_duplicata() -> None:
    repository = FinancialRepository()
    captured: dict[str, object] = {}

    def fake_execute_one(sql, params):
        captured["sql"] = sql
        return {"rol": 0.0}

    with patch.object(FinancialRepository, "__enter__", return_value=repository):
        with patch.object(FinancialRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_one", side_effect=fake_execute_one):
                repository.get_rol(
                    GetRolRequest(
                        branch="01",
                        start_date="20260801",
                        end_date="20260828",
                    )
                )

    sql = str(captured["sql"])
    assert "F4D.F4_DUPLIC" in sql
    assert "F4X.F4_DUPLIC" in sql
    assert "D1.D1_CF IN ('1201', '2201')" in sql
    # tipo D só conta com duplicata do TES
    assert "D1.D1_TIPO = 'D'" in sql
    assert "ISNULL(F4D.F4_DUPLIC, '') = 'S'" in sql
    assert "ISNULL(F4X.F4_DUPLIC, '') = 'S'" in sql
    # predicado antigo amplo (tipo D sem DUPLIC) não pode permanecer
    assert "OR D1.D1_TIPO = 'D'\n                )" not in sql
    assert "OR D1X.D1_TIPO = 'D'\n                                )" not in sql
