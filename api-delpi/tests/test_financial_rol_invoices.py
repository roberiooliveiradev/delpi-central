from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.dto.financial.get_rol_request import GetRolRequest
from app.application.use_cases.financial.get_rol_invoices_use_case import (
    DEFAULT_ROL_INVOICE_LIMIT,
    GetRolInvoicesUseCase,
)
from app.infrastructure.persistence.totvs.financial_repositories.financial_repository import (
    FinancialRepository,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


def test_list_rol_invoices_sql_reuses_sale_and_return_eligibility() -> None:
    repository = FinancialRepository()
    captured: dict[str, object] = {}

    def fake_execute_query(sql, params):
        captured["sql"] = sql
        captured["params"] = params
        return []

    with patch.object(FinancialRepository, "__enter__", return_value=repository):
        with patch.object(FinancialRepository, "__exit__", return_value=False):
            with patch.object(repository, "execute_query", side_effect=fake_execute_query):
                repository.list_rol_invoices(
                    GetRolRequest(
                        branch="01",
                        start_date="2026-08-01",
                        end_date="2026-08-31",
                    ),
                    limit=100,
                )

    sql = str(captured["sql"])
    params = captured["params"]
    assert isinstance(params, tuple)
    assert params[0] == 101
    assert "SELECT TOP (?)" in sql
    assert "UNION ALL" in sql
    assert "GROUP BY D2.D2_FILIAL, D2.D2_DOC, D2.D2_SERIE, D2.D2_CLIENTE, D2.D2_LOJA" in sql
    assert "GROUP BY D1.D1_FILIAL, D1.D1_DOC, D1.D1_SERIE, D1.D1_FORNECE, D1.D1_LOJA" in sql
    assert "D1.D1_CF IN ('1201', '2201')" in sql
    assert "ISNULL(F4D.F4_DUPLIC, '') = 'S'" in sql
    assert "F4.F4_DUPLIC" in sql
    assert "5911" in sql


def test_get_rol_invoices_use_case_maps_and_truncates() -> None:
    repository = MagicMock()
    repository.list_rol_invoices.return_value = [
        {
            "kind": "sale",
            "branch": "01",
            "issue_date": "20260802",
            "invoice_number": "000123",
            "series": "1",
            "customer_code": "000001",
            "customer_store": "01",
            "customer_name": "WEG",
            "gross": 120.0,
            "discounts": 10.0,
            "returns": 0.0,
            "taxes": 20.0,
            "rol": 100.0,
        },
        {
            "kind": "return",
            "branch": "01",
            "issue_date": "20260803",
            "invoice_number": "000050",
            "series": "1",
            "customer_code": "000002",
            "customer_store": "01",
            "customer_name": "Cliente",
            "gross": 0.0,
            "discounts": 0.0,
            "returns": 25.0,
            "taxes": 0.0,
            "rol": -25.0,
        },
        {
            "kind": "sale",
            "branch": "01",
            "issue_date": "20260804",
            "invoice_number": "000124",
            "series": "1",
            "customer_code": "000003",
            "customer_store": "01",
            "customer_name": "Extra",
            "gross": 10.0,
            "discounts": 0.0,
            "returns": 0.0,
            "taxes": 0.0,
            "rol": 10.0,
        },
    ]
    result = GetRolInvoicesUseCase(repository).execute(
        GetRolRequest(branch="01", start_date="2026-08-01", end_date="2026-08-31"),
        limit=2,
    )

    assert result["truncated"] is True
    assert result["pagination"]["is_complete"] is False
    assert result["pagination"]["returned"] == 2
    assert len(result["items"]) == 2
    assert result["items"][0]["issue_date"] == "2026-08-02"
    assert result["items"][1]["kind"] == "return"
    assert result["totals"]["rol"] == 75.0
    assert result["totals"]["returns"] == 25.0
    repository.list_rol_invoices.assert_called_once()


@patch("app.interface.http.routes.financial.financial_routes.build_get_rol_invoices_use_case")
def test_get_financial_rol_invoices_route_contract(mock_build) -> None:
    import app.interface.http.routes.financial.financial_routes as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = {
        "branch": "01",
        "start_date": "2026-08-01",
        "end_date": "2026-08-31",
        "items": [
            {
                "kind": "sale",
                "branch": "01",
                "issue_date": "2026-08-02",
                "invoice_number": "000123",
                "series": "1",
                "customer_code": "000001",
                "customer_store": "01",
                "customer_name": "WEG",
                "gross": 120.0,
                "discounts": 10.0,
                "returns": 0.0,
                "taxes": 20.0,
                "rol": 100.0,
            }
        ],
        "truncated": False,
        "totals": {
            "count": 1,
            "gross": 120.0,
            "discounts": 10.0,
            "returns": 0.0,
            "taxes": 20.0,
            "rol": 100.0,
        },
        "pagination": {
            "limit": DEFAULT_ROL_INVOICE_LIMIT,
            "offset": 0,
            "returned": 1,
            "is_complete": True,
        },
    }
    mock_build.return_value = use_case

    response = router_mod.get_rol_invoices(
        branch="01",
        start_date="2026-08-01",
        end_date="2026-08-31",
        limit=DEFAULT_ROL_INVOICE_LIMIT,
    )
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="get_financial_rol_invoices",
        shape="paged_list",
        entity="financial_rol_invoice",
    )
    assert payload["data"]["items"][0]["invoice_number"] == "000123"
    use_case.execute.assert_called_once()
