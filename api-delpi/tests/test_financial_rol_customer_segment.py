from unittest.mock import patch

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)


def test_get_rol_applies_weg_segment_to_sales_and_returns() -> None:
    repository = FinancialRepository()
    captured: dict[str, object] = {}

    def fake_execute_one(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return {"rol_with_ipi": 100.0}

    with patch.object(FinancialRepository, "__enter__", return_value=repository):
        with patch.object(FinancialRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_one", side_effect=fake_execute_one):
                result = repository.get_rol(
                    GetRolRequest(
                        branch="02",
                        start_date="20260501",
                        end_date="20260531",
                        customer_segment="weg",
                    )
                )

    sql = str(captured["sql"])
    assert "D2.D2_CLIENTE" in sql
    assert "D1.D1_FORNECE" in sql
    assert "000001" in sql
    assert result["rol_with_ipi"] == 100.0


def test_get_rol_without_segment_omits_weg_predicate() -> None:
    repository = FinancialRepository()
    captured: dict[str, object] = {}

    def fake_execute_one(sql, params):
        captured["sql"] = sql
        return {"rol_with_ipi": 0.0}

    with patch.object(FinancialRepository, "__enter__", return_value=repository):
        with patch.object(FinancialRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_one", side_effect=fake_execute_one):
                repository.get_rol(
                    GetRolRequest(
                        branch="01",
                        start_date="20260501",
                        end_date="20260531",
                    )
                )

    sql = str(captured["sql"])
    assert sql.count("000001") == 0
