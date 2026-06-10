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
