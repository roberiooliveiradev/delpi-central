from app.domain.services.chat_presentation_visual_bundle_service import (
    ChatPresentationVisualBundleService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_cost_impact_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_cost_impact_simulation_90261255.json")
    path = "/products/90261255/cost-impact-simulation"
    tables = presenter.build_cost_impact_simulation_table_presentations(envelope["data"], path)

    assert len(tables) >= 2
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "list" for table in tables)


def test_visual_bundle_enriches_cost_impact_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_cost_impact_simulation_90261255.json")
    path = "/products/90261255/cost-impact-simulation"
    tables = presenter.build_cost_impact_simulation_table_presentations(envelope["data"], path)
    text = presenter._build_cost_impact_simulation_text_presentation(envelope["data"], path)

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
