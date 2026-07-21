"""Unit — janela 30d e provider de rupturas (Delpi Reports Fase 2)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock

from app.application.services.supplies.safety_stock_shortage_30d_aggregation_service import (
    SafetyStockShortage30dAggregationService,
)
from app.domain.services.reports.providers.safety_stock_shortage_30d_provider import (
    SafetyStockShortage30dProvider,
)
from app.domain.services.reports.safety_stock_shortage_30d_rules import (
    balance_at_first_shortage,
    shortage_date_in_horizon,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    build_stock_projection,
)


def test_shortage_date_in_horizon_includes_boundaries() -> None:
    as_of = date(2026, 7, 16)
    assert shortage_date_in_horizon("2026-07-16", as_of=as_of, horizon_days=30) is True
    assert shortage_date_in_horizon("2026-08-15", as_of=as_of, horizon_days=30) is True
    assert shortage_date_in_horizon("2026-08-16", as_of=as_of, horizon_days=30) is False
    assert shortage_date_in_horizon("2026-07-15", as_of=as_of, horizon_days=30) is False
    assert shortage_date_in_horizon(None, as_of=as_of, horizon_days=30) is False


def test_balance_at_first_shortage_matches_projection_fixture() -> None:
    """Paridade com test_projection_detects_temporary_shortage_before_purchase_arrives."""
    as_of = date(2026, 7, 16)
    projection = build_stock_projection(
        available_stock=100.0,
        safety_stock=0.0,
        enriched_orders=[
            {
                "order_number": "PC200",
                "order_item": "01",
                "warehouse": "01",
                "expected_delivery_date": "2026-07-30",
                "open_quantity_primary_unit": 200.0,
                "coverage_eligible": True,
                "unit_compatible": True,
                "supplier_name": "TRAMAR",
            }
        ],
        enriched_commitments=[
            {
                "production_order": "OP150",
                "warehouse": "01",
                "commitment_date": "2026-07-20",
                "open_quantity_primary_unit": 150.0,
                "projection_eligible": True,
                "unit_compatible": True,
            }
        ],
        as_of_date=as_of,
    )
    summary = projection["summary"]
    assert summary["first_shortage_date"] == "2026-07-20"
    assert balance_at_first_shortage(projection) == -50.0
    assert shortage_date_in_horizon(
        summary["first_shortage_date"],
        as_of=as_of,
        horizon_days=30,
    )


def test_aggregation_includes_in_window_excludes_outside() -> None:
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "IN_WINDOW",
            "product_description": "Dentro",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
        },
        {
            "product_code": "OUT_WINDOW",
            "product_description": "Fora",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
        },
        {
            "product_code": "NO_SHORTAGE",
            "product_description": "Ok",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
        },
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = []
    repo.fetch_open_commitments_for_branch.return_value = [
        {
            "product_code": "IN_WINDOW",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
        },
        {
            "product_code": "OUT_WINDOW",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260901",
            "production_order": "OP2",
        },
    ]

    service = SafetyStockShortage30dAggregationService(repo)
    rows, meta = service.collect_rows(
        branch="01",
        horizon_days=30,
        as_of_date=as_of,
    )

    assert meta["materialsScanned"] == 3
    assert meta["shortageCount"] == 1
    assert len(rows) == 1
    assert rows[0]["product_code"] == "IN_WINDOW"
    assert rows[0]["first_shortage_date"] == "2026-07-20"
    assert rows[0]["shortage_balance"] == -50.0
    repo.fetch_materials_for_projection_batch.assert_called_once()
    repo.fetch_open_purchase_orders_for_branch.assert_called_once_with(branch="01")
    repo.fetch_open_commitments_for_branch.assert_called_once_with(branch="01")


def test_provider_collect_and_render_email() -> None:
    aggregation = MagicMock()
    aggregation.collect_rows.return_value = (
        [
            {
                "product_code": "10020113",
                "product_description": "MP",
                "branch": "01",
                "available_stock": 10.0,
                "first_shortage_date": "2026-07-20",
                "shortage_balance": -5.0,
                "observation": "",
            }
        ],
        {
            "branch": "01",
            "horizonDays": 30,
            "asOfDate": "2026-07-16",
            "materialsScanned": 1,
            "shortageCount": 1,
        },
    )
    provider = SafetyStockShortage30dProvider(aggregation)
    assert provider.key == "safety_stock_shortage_30d"
    dataset = provider.collect({"branch": "01", "horizonDays": 30})
    assert dataset.row_count == 1
    email = provider.render_email(dataset)
    assert "Jaraguá do Sul/SC" in email.subject
    assert "10020113" in email.html_body
    assert "<table" in email.html_body
    assert "cid:delpi-logo" in email.html_body
    assert "#013866" in email.html_body
    assert "#30B8EC" in email.html_body
    assert "www.delpi.com.br" in email.html_body
    assert "Gerado pelo Minha DELPI" in email.html_body
    assert email.attachments == ()
    assert "20/07/2026" in email.html_body
    assert "16/07/2026" in email.html_body
    assert "2026-07-20" not in email.html_body
    assert "min-width:96px" in email.html_body
    assert "width:36%" in email.html_body
    assert "Jaraguá do Sul/SC" in email.html_body
    assert ">Filial<" not in email.html_body
    assert "filial 01" not in email.html_body.lower()


def test_provider_render_email_includes_logo_attachment() -> None:
    from app.domain.services.reports.report_types import ReportAttachment

    aggregation = MagicMock()
    aggregation.collect_rows.return_value = (
        [],
        {"branch": "02", "horizonDays": 30, "asOfDate": "2026-07-21"},
    )
    logo = ReportAttachment(
        name="logo_delpi.png",
        content_type="image/png",
        content_base64="abc",
        is_inline=True,
        content_id="delpi-logo",
    )
    provider = SafetyStockShortage30dProvider(aggregation, logo_attachment=logo)
    email = provider.render_email(provider.collect({"branch": "02"}))
    assert email.attachments == (logo,)
    assert "Nenhuma ruptura" in email.html_body
    assert "cid:delpi-logo" in email.html_body
    assert "21/07/2026" in email.html_body
    assert "2026-07-21" not in email.html_body
    assert "Rio Bananal/ES" in email.html_body
    assert "Rio Bananal/ES" in email.subject
