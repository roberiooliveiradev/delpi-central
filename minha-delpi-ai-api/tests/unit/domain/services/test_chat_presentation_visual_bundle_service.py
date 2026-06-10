from app.domain.services.chat_presentation_visual_bundle_service import (
    ChatPresentationVisualBundleService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_visual_bundle_enriches_stock_with_all_auxiliary_slots() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    path = "/products/90269001/stock"
    tables = presenter.build_stock_table_presentations(envelope["data"], path)
    text = presenter._build_stock_text_presentation(envelope["data"], path)

    metadata = {
        "presentation": tables[-1] if tables else None,
        "tablePresentations": tables,
        "tablePresentation": tables[-1] if len(tables) > 1 else tables[0] if tables else None,
        "profileTablePresentation": tables[0] if tables else None,
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
