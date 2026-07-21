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
    build_next_purchase_text,
    build_sample_observation,
    build_third_party_observation,
    compose_observation_parts,
    finished_product_code_at_first_shortage,
    is_sample_finished_product,
    next_eligible_purchase_order,
    should_annotate_third_party_observation,
    shortage_date_in_horizon,
)
from app.domain.services.supplies.safety_stock_stock_projection_service import (
    build_stock_projection,
)
from app.infrastructure.persistence.totvs.supplies_repositories.safety_stock_sql import (
    last_inbound_party_names_sql,
    materials_for_projection_batch_sql,
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
    assert rows[0]["next_purchase"] == "Sem pedido elegível"
    assert rows[0]["observation"] == ""
    repo.fetch_materials_for_projection_batch.assert_called_once()
    repo.fetch_open_purchase_orders_for_branch.assert_called_once_with(branch="01")
    repo.fetch_open_commitments_for_branch.assert_called_once_with(branch="01")


def test_aggregation_excludes_negative_stock_without_open_commitment() -> None:
    """Saldo negativo residual sem empenho não entra no relatório de ruptura."""
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "100700011",
            "product_description": "Sem demanda",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": -12.0,
            "safety_stock": 0.0,
        },
        {
            "product_code": "WITH_COMMITMENT",
            "product_description": "Com demanda",
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
            "product_code": "WITH_COMMITMENT",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
        },
    ]

    rows, meta = SafetyStockShortage30dAggregationService(repo).collect_rows(
        branch="01",
        horizon_days=30,
        as_of_date=as_of,
    )
    assert meta["materialsScanned"] == 2
    assert [row["product_code"] for row in rows] == ["WITH_COMMITMENT"]


def test_next_eligible_purchase_order_picks_earliest_delivery() -> None:
    chosen = next_eligible_purchase_order(
        [
            {
                "order_number": "PC100",
                "order_item": "01",
                "coverage_eligible": True,
                "expected_delivery_date": "2026-08-10",
                "supplier_name": "TARDE",
                "open_quantity_primary_unit": 10.0,
            },
            {
                "order_number": "PC050",
                "order_item": "02",
                "coverage_eligible": False,
                "expected_delivery_date": "2026-07-01",
                "supplier_name": "IGNORADO",
                "open_quantity_primary_unit": 99.0,
            },
            {
                "order_number": "PC200",
                "order_item": "01",
                "coverage_eligible": True,
                "expected_delivery_date": "2026-07-30",
                "supplier_name": "TRAMAR",
                "open_quantity_primary_unit": 200.0,
            },
        ]
    )
    assert chosen is not None
    assert chosen["order_number"] == "PC200"
    assert (
        build_next_purchase_text(
            enriched_orders=[chosen],
            product_unit="MT",
            summary={},
        )
        == "PC200/01 — TRAMAR — Entrega 30/07/2026 — 200 MT"
    )


def test_aggregation_next_purchase_includes_qty_and_blank_observation() -> None:
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "WITH_PO",
            "product_description": "Com pedido",
            "unit": "MT",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
        },
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = [
        {
            "product_code": "WITH_PO",
            "order_number": "PC200",
            "order_item": "01",
            "warehouse": "01",
            "unit": "MT",
            "open_quantity": 200.0,
            "expected_delivery_date": "2026-07-30",
            "supplier_name": "TRAMAR",
            "supplier_code": "0001",
        },
    ]
    repo.fetch_open_commitments_for_branch.return_value = [
        {
            "product_code": "WITH_PO",
            "warehouse": "01",
            "unit": "MT",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
        },
    ]

    rows, _meta = SafetyStockShortage30dAggregationService(repo).collect_rows(
        branch="01",
        horizon_days=30,
        as_of_date=as_of,
    )
    assert len(rows) == 1
    assert rows[0]["next_purchase"] == "PC200/01 — TRAMAR — Entrega 30/07/2026 — 200 MT"
    assert rows[0]["observation"] == ""
    assert rows[0]["unit"] == "MT"


def test_provider_collect_and_render_email() -> None:
    aggregation = MagicMock()
    aggregation.collect_rows.return_value = (
        [
            {
                "product_code": "10020113",
                "product_description": "MP",
                "branch": "01",
                "unit": "MT",
                "available_stock": 10.0,
                "first_shortage_date": "2026-07-20",
                "shortage_balance": -5.0,
                "next_purchase": "PC200/01 — TRAMAR — Entrega 30/07/2026 — 200 MT",
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
    assert "width:26%" in email.html_body
    assert "text-align:center;vertical-align:middle" in email.html_body
    assert "Próximo Pedido" in email.html_body
    assert "Observação" in email.html_body
    assert "10 MT" in email.html_body
    assert "-5 MT" in email.html_body
    assert "PC200/01" in email.html_body
    assert "TRAMAR" in email.html_body
    assert "Entrega 30/07/2026" in email.html_body
    assert "200 MT" in email.html_body
    assert "font-weight:700" in email.html_body
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


def test_third_party_observation_helpers() -> None:
    assert should_annotate_third_party_observation(branch="01", material_type="2")
    assert should_annotate_third_party_observation(branch="01", material_type=" 2 ")
    assert not should_annotate_third_party_observation(branch="02", material_type="2")
    assert not should_annotate_third_party_observation(branch="01", material_type="1")
    assert (
        build_third_party_observation("ACME INDUSTRIA")
        == "Material de terceiro - ACME INDUSTRIA"
    )
    assert (
        build_third_party_observation("")
        == "Material de terceiro - não identificado"
    )


def test_sample_observation_helpers() -> None:
    assert is_sample_finished_product("80123456")
    assert is_sample_finished_product("8")
    assert not is_sample_finished_product("70123456")
    assert not is_sample_finished_product("")
    assert build_sample_observation("80123456") == "AMOSTRA - 80123456"
    assert (
        compose_observation_parts(
            "Material de terceiro - WEG",
            "AMOSTRA - 80123456",
        )
        == "Material de terceiro - WEG | AMOSTRA - 80123456"
    )


def test_finished_product_code_at_first_shortage_from_projection() -> None:
    as_of = date(2026, 7, 16)
    projection = build_stock_projection(
        available_stock=100.0,
        safety_stock=0.0,
        enriched_orders=[],
        enriched_commitments=[
            {
                "production_order": "OP150",
                "warehouse": "01",
                "commitment_date": "2026-07-20",
                "open_quantity_primary_unit": 150.0,
                "projection_eligible": True,
                "unit_compatible": True,
                "finished_product_code": "80123456",
            }
        ],
        as_of_date=as_of,
    )
    assert finished_product_code_at_first_shortage(projection) == "80123456"


def test_sql_includes_material_type_and_last_inbound_party() -> None:
    materials_sql = materials_for_projection_batch_sql(where_sql="")
    assert "B1_TPMAT" in materials_sql
    assert "material_type" in materials_sql
    inbound_sql = last_inbound_party_names_sql(placeholders="?, ?")
    assert "SD1010" in inbound_sql
    assert "SA1010" in inbound_sql
    assert "A1_NREDUZ" in inbound_sql
    assert "A1_NOME" in inbound_sql
    assert "D1_TIPO = 'B'" in inbound_sql
    assert "party_name" in inbound_sql
    assert "SA2010" not in inbound_sql
    assert "D1_TIPO = 'N'" not in inbound_sql


def test_aggregation_third_party_observation_branch_01() -> None:
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "TP_MAT",
            "product_description": "Terceiro",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
            "material_type": "2",
        },
        {
            "product_code": "OWN_MAT",
            "product_description": "Próprio",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
            "material_type": "1",
        },
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = []
    repo.fetch_open_commitments_for_branch.return_value = [
        {
            "product_code": "TP_MAT",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
        },
        {
            "product_code": "OWN_MAT",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP2",
        },
    ]
    repo.fetch_last_inbound_party_names.return_value = {"TP_MAT": "CLIENTE XYZ"}

    rows, _meta = SafetyStockShortage30dAggregationService(repo).collect_rows(
        branch="01",
        horizon_days=30,
        as_of_date=as_of,
    )
    by_code = {row["product_code"]: row for row in rows}
    assert by_code["TP_MAT"]["observation"] == "Material de terceiro - CLIENTE XYZ"
    assert by_code["OWN_MAT"]["observation"] == ""
    repo.fetch_last_inbound_party_names.assert_called_once_with(
        branch="01",
        product_codes=["TP_MAT"],
    )


def test_aggregation_third_party_skips_observation_on_branch_02() -> None:
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "TP_MAT",
            "product_description": "Terceiro",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
            "material_type": "2",
        },
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = []
    repo.fetch_open_commitments_for_branch.return_value = [
        {
            "product_code": "TP_MAT",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
        },
    ]

    rows, _meta = SafetyStockShortage30dAggregationService(repo).collect_rows(
        branch="02",
        horizon_days=30,
        as_of_date=as_of,
    )
    assert len(rows) == 1
    assert rows[0]["observation"] == ""
    repo.fetch_last_inbound_party_names.assert_not_called()


def test_aggregation_sample_observation_when_finished_starts_with_8() -> None:
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "MP_SAMPLE",
            "product_description": "MP amostra",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
            "material_type": "1",
        },
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = []
    repo.fetch_open_commitments_for_branch.return_value = [
        {
            "product_code": "MP_SAMPLE",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
            "finished_product_code": "80123456",
        },
    ]

    rows, _meta = SafetyStockShortage30dAggregationService(repo).collect_rows(
        branch="01",
        horizon_days=30,
        as_of_date=as_of,
    )
    assert len(rows) == 1
    assert rows[0]["observation"] == "AMOSTRA - 80123456"


def test_aggregation_combines_third_party_and_sample_observation() -> None:
    as_of = date(2026, 7, 16)
    repo = MagicMock()
    repo.fetch_materials_for_projection_batch.return_value = [
        {
            "product_code": "TP_SAMPLE",
            "product_description": "Terceiro amostra",
            "unit": "PC",
            "secondary_unit": "",
            "conversion_factor": None,
            "conversion_type": "",
            "available_stock": 100.0,
            "safety_stock": 0.0,
            "material_type": "2",
        },
    ]
    repo.fetch_open_purchase_orders_for_branch.return_value = []
    repo.fetch_open_commitments_for_branch.return_value = [
        {
            "product_code": "TP_SAMPLE",
            "warehouse": "01",
            "unit": "PC",
            "open_quantity": 150.0,
            "commitment_date": "20260720",
            "production_order": "OP1",
            "finished_product_code": "80999999",
        },
    ]
    repo.fetch_last_inbound_party_names.return_value = {"TP_SAMPLE": "WEG AUTOMACAO"}

    rows, _meta = SafetyStockShortage30dAggregationService(repo).collect_rows(
        branch="01",
        horizon_days=30,
        as_of_date=as_of,
    )
    assert rows[0]["observation"] == (
        "Material de terceiro - WEG AUTOMACAO | AMOSTRA - 80999999"
    )


def test_provider_renders_third_party_observation() -> None:
    aggregation = MagicMock()
    aggregation.collect_rows.return_value = (
        [
            {
                "product_code": "TP001",
                "product_description": "MP terceiro",
                "branch": "01",
                "unit": "PC",
                "available_stock": 1.0,
                "first_shortage_date": "2026-07-20",
                "shortage_balance": -1.0,
                "next_purchase": "Sem pedido elegível",
                "observation": "Material de terceiro - CLIENTE XYZ",
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
    email = SafetyStockShortage30dProvider(aggregation).render_email(
        SafetyStockShortage30dProvider(aggregation).collect({"branch": "01"})
    )
    assert "Material de terceiro - CLIENTE XYZ" in email.html_body
