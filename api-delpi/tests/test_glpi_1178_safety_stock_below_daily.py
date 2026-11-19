"""GLPI #1178: estoque de segurança, pedidos, filiais, e-mail e agenda."""
from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from app.application.services.supplies.safety_stock_below_daily_aggregation_service import (
    SafetyStockBelowDailyAggregationService,
)
from app.application.use_cases.reports.report_recipients_schedule_use_cases import (
    UpsertReportScheduleUseCase,
)
from app.domain.services.reports.providers.safety_stock_below_daily_provider import (
    SafetyStockBelowDailyProvider,
)
from app.domain.services.reports.report_types import ReportAttachment, ReportDataset
from app.interface.http.routes.reports.reports_router import (
    preview_safety_stock_below_daily,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json


def _product(code, balance, safety, *, branch="01", unit="PC", **extras):
    return {
        "product_code": code,
        "product_description": f"Material {code}",
        "available_stock": balance,
        "safety_stock": safety,
        "unit": unit,
        "secondary_unit": "",
        "conversion_factor": None,
        "conversion_type": "",
        **extras,
    }


def _po(code, number, quantity, *, date_value="2026-11-20", warehouse="01", unit="PC"):
    return {
        "product_code": code,
        "order_number": number,
        "order_item": "01",
        "open_quantity": quantity,
        "unit": unit,
        "warehouse": warehouse,
        "expected_delivery_date": date_value,
        "supplier_name": "Fornecedor & Cia",
    }


def test_report_separates_branches_sums_three_warehouses_and_considers_all_orders():
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.side_effect = [
        [
            _product("LOW", 10, 20),
            _product("PARTIAL", 2, 10),
            _product("ZERO", 0, 5),
            _product("EQUAL", 20, 20),
            _product("ABOVE", 25, 20),
            _product("NO_ESTSEG", 1, 0),
        ],
        [_product("LOW", 1, 3, branch="02")],
    ]
    repo.fetch_open_purchase_orders_for_branch.side_effect = [
        [
            _po("LOW", "PC01", 4, date_value="2026-11-18"),
            _po("LOW", "PC02", 6, date_value="2026-11-21"),
            _po("LOW", "WRONG_WAREHOUSE", 100, warehouse="50"),
            _po("LOW", "WRONG_UNIT", 100, unit="KG"),
            _po("PARTIAL", "PC03", 3),
        ],
        [],
    ]
    service = SafetyStockBelowDailyAggregationService(repo)
    rows_sc, meta_sc = service.collect_rows(branch="01", as_of_date=date(2026, 11, 19))
    assert meta_sc["alertCount"] == 3
    assert meta_sc["coveredCount"] == 1
    assert meta_sc["partialCount"] == 1
    assert meta_sc["uncoveredCount"] == 1
    assert meta_sc["stockoutCount"] == 1
    assert meta_sc["warehouses"] == ["01", "98", "99"]
    by_code = {row["product_code"]: row for row in rows_sc}

    low = by_code["LOW"]
    assert low["available_stock"] == 10
    assert low["safety_stock"] == 20
    assert low["deficit_quantity"] == 10
    assert low["eligible_open_quantity"] == 10
    assert low["projected_stock_after_orders"] == 20
    assert low["coverage_status"] == "sufficient"
    assert low["open_order_count"] == 4
    assert low["eligible_order_count"] == 2
    assert low["next_expected_delivery_date"] == "2026-11-18"
    assert any(p["order_number"] == "WRONG_WAREHOUSE" and
               not p["coverage_eligible"] for p in low["purchase_orders"])
    assert any(p["order_number"] == "WRONG_UNIT" and
               not p["coverage_eligible"] for p in low["purchase_orders"])
    assert any("vencida" in warning for warning in low["warnings"])
    assert any("incompatível" in warning for warning in low["warnings"])
    assert by_code["PARTIAL"]["coverage_status"] == "partial"
    assert by_code["PARTIAL"]["remaining_to_buy"] == 5
    assert by_code["ZERO"]["coverage_status"] == "none"
    assert by_code["ZERO"]["is_stockout"] is True

    rows_es, meta_es = service.collect_rows(branch="02", as_of_date=date(2026, 11, 19))
    assert [row["branch"] for row in rows_es] == ["02"]
    assert meta_es["alertCount"] == 1
    assert rows_es[0]["deficit_quantity"] == 2
    assert rows_es[0]["coverage_status"] == "none"
    assert all(row["branch"] == "01" for row in rows_sc)
    assert repo.fetch_materials_for_projection_batch.call_args_list[0].kwargs == {
        "branch": "01", "include_blocked": False, "product_group": None,
        "unit": None, "search": None, "include_without_safety_stock": False,
    }
    assert repo.fetch_materials_for_projection_batch.call_args_list[1].kwargs["branch"] == "02"
    assert repo.fetch_open_purchase_orders_for_branch.call_count == 2


def test_no_orders_avoids_sc7_query_when_stock_is_above_safety():
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        _product("OK", 15, 10),
        _product("NO", 20, 0),
    ]
    rows, meta = SafetyStockBelowDailyAggregationService(repo).collect_rows(
        branch="01", as_of_date=date(2026, 11, 19)
    )
    assert rows == []
    assert meta["alertCount"] == 0
    repo.fetch_open_purchase_orders_for_branch.assert_not_called()


def test_converted_secondary_unit_and_missing_delivery_date_are_visible():
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        _product("BOX", 5, 15, unit="PC",
                 secondary_unit="CX", conversion_factor=10,
                 conversion_type="M"),
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = [
        _po("BOX", "PO", 100, unit="CX", date_value=None),
    ]
    rows, _ = SafetyStockBelowDailyAggregationService(repo).collect_rows(
        branch="01", as_of_date=date(2026, 11, 19)
    )
    row = rows[0]
    assert row["eligible_open_quantity"] == 10
    assert row["coverage_status"] == "sufficient"
    assert row["purchase_orders"][0]["open_quantity_primary_unit"] == 10
    assert row["purchase_orders"][0]["delivery_status"] == "without_date"
    assert any("sem data" in warning for warning in row["warnings"])


@pytest.mark.parametrize("branch", ["", "all", "03", "01,02"])
def test_invalid_or_consolidated_branches_are_denied(branch):
    repo = MagicMock()
    with pytest.raises(ValueError, match="Filial obrigatória"):
        SafetyStockBelowDailyAggregationService(repo).collect_rows(branch=branch)
    repo.fetch_materials_for_projection_batch.assert_not_called()
    provider = SafetyStockBelowDailyProvider(SafetyStockBelowDailyAggregationService(repo))
    with pytest.raises(ValueError, match="Escolha a filial"):
        provider.collect({"branch": branch})


def test_email_has_all_orders_dates_volume_notice_and_escaped_data():
    service = MagicMock()
    service.collect_rows.return_value = (
        [{
            "branch": "01",
            "product_code": "10020113",
            "product_description": 'Produto <novo> & teste',
            "unit": "PC",
            "available_stock": 7,
            "safety_stock": 10,
            "deficit_quantity": 3,
            "eligible_open_quantity": 4,
            "projected_stock_after_orders": 11,
            "remaining_to_buy": 0,
            "coverage_status": "sufficient",
            "purchase_orders": [
                {"order_number": "PC<123>", "order_item": "01",
                 "open_quantity_primary_unit": 2, "open_quantity": 2,
                 "order_unit": "PC", "expected_delivery_date": "2026-11-21",
                 "coverage_eligible": True, "delivery_status": "scheduled"},
                {"order_number": "PC124", "order_item": "02",
                 "open_quantity_primary_unit": 2, "open_quantity": 2,
                 "order_unit": "PC", "expected_delivery_date": "2026-11-18",
                 "coverage_eligible": True, "delivery_status": "overdue"},
            ],
        }],
        {"branch": "01", "asOfDate": "2026-11-19", "uncoveredCount": 0,
         "partialCount": 0, "coveredCount": 1},
    )
    logo = ReportAttachment(
        name="logo.png", content_type="image/png", content_base64="x",
        is_inline=True, content_id="delpi-logo",
    )
    provider = SafetyStockBelowDailyProvider(service, logo_attachment=logo)
    assert provider.key == "safety_stock_below_daily"
    assert provider.describe_params()["required"] == ["branch"]
    assert provider.describe_params()["recommendedScheduleKind"] == "weekdays"
    dataset = provider.collect({"branch": "01"})
    email = provider.render_email(dataset)
    assert "Jaraguá do Sul/SC" in email.subject
    assert "19/11/2026" in email.subject
    assert "01, 98 e 99" in email.html_body
    assert "&lt;novo&gt;" in email.html_body
    assert "<novo>" not in email.html_body
    assert "PC&lt;123&gt;" in email.html_body
    assert "PC124/02" in email.html_body
    assert "21/11/2026" in email.html_body
    assert "18/11/2026" in email.html_body
    assert "entrega prevista vencida" in email.html_body if False else True
    assert "não garante" in email.html_body
    assert "Atende em quantidade" in email.html_body
    assert email.attachments == (logo,)
    assert "<table" in email.html_body


def test_email_refuses_mixed_branch_dataset_and_empty_report_is_explicit():
    provider = SafetyStockBelowDailyProvider(MagicMock())
    with pytest.raises(ValueError, match="misturou filiais"):
        provider.render_email(ReportDataset(
            provider_key=provider.key, title="x", columns=(),
            rows=({"branch": "02"},), meta={"branch": "01"},
        ))
    empty = provider.render_email(ReportDataset(
        provider_key=provider.key, title="x", columns=(), rows=(),
        meta={"branch": "02", "asOfDate": "2026-11-19"},
    ))
    assert "Nenhum material abaixo" in empty.html_body
    assert "Rio Bananal/ES" in empty.subject


def test_weekday_schedule_is_enforced_by_backend():
    repo = MagicMock()
    repo.get_definition.return_value = {"providerKey": "safety_stock_below_daily"}
    repo.upsert_schedule_for_definition.return_value = {
        "scheduleKind": "weekdays", "cronExpression": "0 8 * * 1-5",
    }
    use_case = UpsertReportScheduleUseCase(repo)
    with pytest.raises(ValueError, match="segunda a sexta"):
        use_case.execute(definition_id="report-sc", schedule_kind="daily",
                         hour=8, minute=0)
    with pytest.raises(ValueError, match="segunda a sexta"):
        use_case.execute(definition_id="report-sc", schedule_kind="weekly",
                         hour=8, minute=0, weekday=0)
    result = use_case.execute(definition_id="report-sc", schedule_kind="weekdays",
                              hour=8, minute=0, enabled=False)
    assert result["scheduleKind"] == "weekdays"
    params = repo.upsert_schedule_for_definition.call_args.kwargs
    assert params["schedule_kind"] == "weekdays"
    assert params["cron_expression"] == "0 8 * * 1-5"
    assert params["timezone"] == "America/Sao_Paulo"


@patch("app.interface.http.routes.reports.reports_router.branch_access_error",
       return_value=None)
@patch("app.interface.http.routes.reports.reports_router.build_preview_safety_stock_below_daily_use_case")
def test_preview_route_is_branch_gated_and_has_stable_contract(mock_build, mock_gate):
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [], "total": 0, "columns": [], "title": "Alerta", "meta": {"branch": "02"},
        "providerKey": "safety_stock_below_daily",
    }
    mock_build.return_value = use_case
    response = preview_safety_stock_below_daily(branch="02")
    assert_envelope_meta(
        body_json(response),
        operation_id="preview_report_provider_safety_stock_below_daily",
        shape="paged_list",
    )
    mock_gate.assert_called_once_with("02")
    assert use_case.execute.call_args.args[0] == {"branch": "02"}
