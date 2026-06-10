from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from app.domain.services.external_actions.operational_route_narrative_service import (
    ExternalActionOperationalRouteNarrativeService,
)
from app.domain.services.chat_presentation_visual_bundle_service import (
    ChatPresentationVisualBundleService,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_is_production_started_handles_bool_and_legacy_codes():
    assert ExternalActionOperationalRouteNarrativeService.is_production_started(True)
    assert not ExternalActionOperationalRouteNarrativeService.is_production_started(False)
    assert ExternalActionOperationalRouteNarrativeService.is_production_started("SIM")
    assert not ExternalActionOperationalRouteNarrativeService.is_production_started("NAO")


def test_factory_highlights_treats_bool_production_started_as_started():
    presenter = ExternalActionResultPresenter()
    composite = presenter._composite_analysis()
    root = {
        "factory_status": "OP ABERTA / EM ANDAMENTO",
        "production": {
            "summary": {
                "pa_production_started": True,
                "pi_production_started": False,
                "total_pa_orders": 2,
                "total_pi_orders": 0,
            }
        },
        "shipping": {"summary": {"total_shipped_quantity": 0}},
    }

    highlights = composite._build_factory_highlights(root)
    combined = "\n".join(highlights).lower()

    assert "não foi iniciada" not in combined
    assert "em andamento" in combined


def test_factory_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"
    tables = presenter.build_factory_status_table_presentations(envelope["data"], path)

    assert len(tables) >= 3
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "structure" for table in tables)
    assert any(table.get("role") == "stock" for table in tables)
    assert any(table.get("role") == "list" for table in tables)


def test_factory_stock_tables_identify_raw_materials():
    presenter = ExternalActionResultPresenter()
    composite = presenter._composite_analysis()
    root = {
        "product": {"product_code": "90262017", "description": "CHICOTE"},
        "factory_status": "PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO",
        "raw_material_stock": {
            "items": [
                {
                    "raw_material_code": "10080063",
                    "raw_material_description": "TERM. FASTON",
                    "unit": "PC",
                    "quantity_required_for_one_pa": "3000",
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": "350000",
                    "available_quantity": "350000",
                    "committed_quantity": "0",
                    "reserved_quantity": "0",
                    "has_stock_for_one_pa_label": "Sim",
                },
                {
                    "raw_material_code": "10080063",
                    "raw_material_description": "TERM. FASTON",
                    "unit": "PC",
                    "quantity_required_for_one_pa": "3000",
                    "branch": "02",
                    "warehouse": "01",
                    "current_quantity": "1000",
                    "available_quantity": "1000",
                    "committed_quantity": "0",
                    "reserved_quantity": "0",
                    "has_stock_for_one_pa_label": "Sim",
                },
                {
                    "raw_material_code": "10160002",
                    "raw_material_description": "RESISTOR 120K",
                    "unit": "PC",
                    "quantity_required_for_one_pa": "3000",
                    "branch": "01",
                    "warehouse": "01",
                    "current_quantity": "4638",
                    "available_quantity": "4638",
                    "committed_quantity": "0",
                    "reserved_quantity": "0",
                    "has_stock_for_one_pa_label": "Sim",
                },
            ]
        },
    }
    tables = presenter.build_factory_status_table_presentations(root, "/products/90262017/factory-status")
    stock_tables = [table for table in tables if table.get("role") == "stock"]

    assert len(stock_tables) == 2
    summary = stock_tables[0]
    detail = stock_tables[1]
    summary_keys = {column["key"] for column in summary.get("columns") or []}
    detail_keys = {column["key"] for column in detail.get("columns") or []}

    assert "raw_material_code" in summary_keys
    assert "raw_material_description" in summary_keys
    assert "available_quantity_total" in summary_keys
    assert "raw_material_code" in detail_keys
    assert "raw_material_description" in detail_keys

    faston = next(
        row
        for row in summary.get("rows") or []
        if row.get("raw_material_code") == "10080063"
    )
    assert float(faston.get("available_quantity_total") or 0) == 351000.0
    assert float(faston.get("pa_coverage_estimate") or 0) == 117.0


def test_factory_production_table_includes_operational_columns():
    presenter = ExternalActionResultPresenter()
    root = {
        "product": {"product_code": "90262017"},
        "production": {
            "items": [
                {
                    "production_order": "24589501001",
                    "product_code": "90262017",
                    "description": "CHICOTE",
                    "product_type": "PA",
                    "order_quantity": "0.324",
                    "produced_quantity_sc2": "0.324",
                    "reported_quantity": "2916",
                    "planned_start_date": "20260609",
                    "planned_end_date": "20260609",
                    "actual_end_date": "20260609",
                    "order_production_percent": "100",
                    "production_started_label": "Sim",
                    "branch": "01",
                }
            ]
        },
    }
    tables = presenter.build_factory_status_table_presentations(root, "/products/90262017/factory-status")
    production = next(table for table in tables if table.get("role") == "list")
    keys = {column["key"] for column in production.get("columns") or []}

    assert "order_quantity" in keys
    assert "reported_quantity" in keys
    assert "planned_end_date" in keys
    assert production["rows"][0]["reported_quantity"] == "2916"


def test_factory_highlights_warn_low_mp_coverage():
    presenter = ExternalActionResultPresenter()
    composite = presenter._composite_analysis()
    root = {
        "factory_status": "PA FINALIZADO / LIBERADO PARA EXPEDIÇÃO",
        "structure": {"items": [{"exclusive_raw_material": False}]},
        "raw_material_stock": {
            "items": [
                {
                    "raw_material_code": "10160002",
                    "unit": "PC",
                    "quantity_required_for_one_pa": "3000",
                    "available_quantity": "4638",
                    "has_stock_for_one_pa_label": "Sim",
                }
            ],
            "summary": {"total_without_stock_for_one_pa": 0},
        },
        "shipping": {"summary": {"total_shipped_quantity": 0}},
    }

    highlights = composite._build_factory_highlights(root)
    combined = "\n".join(highlights)

    assert "10160002" in combined
    assert "cobertura baixa" in combined.lower()


def test_visual_bundle_enriches_factory_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")
    path = "/products/90269002/factory-status"
    tables = presenter.build_factory_status_table_presentations(envelope["data"], path)
    text = presenter._build_factory_status_text_presentation(envelope["data"], path)

    metadata = {
        "presentation": tables[1] if len(tables) > 1 else tables[0],
        "tablePresentations": tables,
        "tablePresentation": tables[1] if len(tables) > 1 else tables[0],
        "profileTablePresentation": tables[0],
        "textPresentation": text,
        "availableFormats": ["text", "table"],
    }

    ChatPresentationVisualBundleService.enrich_metadata(
        metadata,
        path=path,
        data=envelope,
        presenter=presenter,
    )

    assert metadata.get("kpiPresentation", {}).get("type") == "kpi"
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
    assert metadata.get("treePresentation", {}).get("type") == "tree"
    assert metadata.get("dashboardPresentation", {}).get("type") == "dashboard"
    assert "kpi" in (metadata.get("availableFormats") or [])
    assert "chart" in (metadata.get("availableFormats") or [])
    assert "tree" in (metadata.get("availableFormats") or [])
    assert "dashboard" in (metadata.get("availableFormats") or [])
