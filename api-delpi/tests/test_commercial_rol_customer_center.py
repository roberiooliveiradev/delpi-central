from unittest.mock import patch

from app.application.dto.commercial.get_rol_by_customer_request import (
    GetRolByCustomerRequest,
)
from app.application.dto.commercial.get_rol_by_product_request import (
    GetRolByProductRequest,
)
from app.application.dto.financial.get_rol_request import GetRolRequest
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_rol_by_customer_repository import (
    CommercialRolByCustomerRepository,
)
from app.infrastructure.persistence.totvs.commercial_repositories.commercial_rol_by_product_repository import (
    CommercialRolByProductRepository,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)


def _capture_one(repository, method_name: str, request):
    captured: dict[str, object] = {}

    def fake_execute_one(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return {"rol": 0.0}

    with patch.object(type(repository), "__enter__", return_value=repository):
        with patch.object(type(repository), "__exit__", return_value=False):
            with patch.object(repository, method_name, side_effect=fake_execute_one):
                getattr(repository, "get_rol")(request)
    return captured


def test_commercial_rol_summary_sql_joins_both_legs_for_center() -> None:
    captured = _capture_one(
        FinancialRepository(),
        "execute_one",
        GetRolRequest(
            branch="01",
            start_date="2026-08-01",
            end_date="2026-08-31",
            customer_centers=["1320"],
        ),
    )
    sql = str(captured["sql"])
    params = tuple(captured["params"])
    assert sql.count("SA7010") == 2
    assert sql.count("D2.D2_COD") >= 1
    assert "D1.D1_COD" in sql
    assert "D1.D1_FORNECE" in sql
    assert "1320" in params
    assert "1700" not in params


def test_commercial_rol_summary_sql_omits_sa7_without_centers() -> None:
    captured = _capture_one(
        FinancialRepository(),
        "execute_one",
        GetRolRequest(
            branch="01",
            start_date="2026-08-01",
            end_date="2026-08-31",
        ),
    )
    assert "SA7010" not in str(captured["sql"])


def test_rol_by_customer_sql_joins_sale_and_return() -> None:
    repository = CommercialRolByCustomerRepository()
    captured: dict[str, object] = {}

    def fake_execute_query(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return []

    request = GetRolByCustomerRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_centers=["1100"],
    )
    with patch.object(CommercialRolByCustomerRepository, "__enter__", return_value=repository):
        with patch.object(CommercialRolByCustomerRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=fake_execute_query):
                repository.get_rol_by_customer(request)

    sql = str(captured["sql"])
    assert sql.count("SA7010") == 2
    assert "D2.D2_CLIENTE" in sql
    assert "D1.D1_FORNECE" in sql
    assert "1100" in tuple(captured["params"])
    assert "1200" not in tuple(captured["params"])
    assert "GROUP BY D2.D2_FILIAL, D2.D2_CLIENTE, D2.D2_LOJA" in sql


def test_rol_by_customer_sql_omits_sa7_without_centers() -> None:
    repository = CommercialRolByCustomerRepository()
    captured: dict[str, object] = {}

    def fake_execute_query(sql, params):
        captured["sql"] = sql
        return []

    request = GetRolByCustomerRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
    )
    with patch.object(CommercialRolByCustomerRepository, "__enter__", return_value=repository):
        with patch.object(CommercialRolByCustomerRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=fake_execute_query):
                repository.get_rol_by_customer(request)

    assert "SA7010" not in str(captured["sql"])


def test_rol_by_product_sql_joins_sale_return_and_countries() -> None:
    repository = CommercialRolByProductRepository()
    captured: list[str] = []

    def fake_execute_query(sql, params):
        captured.append(sql)
        return []

    request = GetRolByProductRequest(
        start_date="2026-08-01",
        end_date="2026-08-31",
        customer_centers=["1320", "1505"],
    )
    with patch.object(CommercialRolByProductRepository, "__enter__", return_value=repository):
        with patch.object(CommercialRolByProductRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=fake_execute_query):
                repository.get_rol_by_product(request)

    assert len(captured) == 2
    main_sql, countries_sql = captured
    assert main_sql.count("SA7010") == 2
    assert "D2.D2_COD" in main_sql
    assert "D1.D1_COD" in main_sql
    assert countries_sql.count("SA7010") == 1
    assert "1700" not in main_sql
