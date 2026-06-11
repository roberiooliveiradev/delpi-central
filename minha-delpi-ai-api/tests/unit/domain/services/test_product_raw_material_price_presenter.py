from app.domain.services.chat_presentation_visual_bundle_service import (
    ChatPresentationVisualBundleService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_raw_material_price_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta(
        "product_raw_material_price_intelligence_10080001.json"
    )
    path = "/products/10080001/raw-material-price-intelligence"
    tables = presenter.build_raw_material_price_intelligence_table_presentations(
        envelope["data"],
        path,
    )

    assert len(tables) >= 3
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "pricing" for table in tables)
    assert any(table.get("role") == "list" for table in tables)
    assert any(table.get("role") == "other" for table in tables)

    history = next(table for table in tables if table.get("role") == "list")
    history_keys = [column["key"] for column in history.get("columns") or []]

    assert "unit_price" in history_keys
    assert "variation_percent" in history_keys
    assert "supplier_code" in history_keys


def test_intelligence_rich_narrative_for_stale_registered_price():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta(
        "product_raw_material_price_intelligence_10080022.json"
    )
    path = "/products/10080022/raw-material-price-intelligence"
    text = presenter._build_raw_material_price_intelligence_text_presentation(
        envelope["data"],
        path,
    )
    markdown = str((text or {}).get("markdown") or "")

    assert "Resumo do produto" in markdown
    assert "ALTA DE PRECO" in markdown
    assert "113" in markdown or "cadastrado" in markdown.lower()
    assert "Recomendação" in markdown
    assert "TE CONNECTIVITY" in markdown

    tables = presenter.build_raw_material_price_intelligence_table_presentations(
        envelope["data"],
        path,
    )
    purchase = next(table for table in tables if table.get("role") == "pricing")
    purchase_keys = [column["key"] for column in purchase.get("columns") or []]

    assert "invoice_number" in purchase_keys
    assert "supplier_part_number" in purchase_keys


def test_visual_bundle_enriches_raw_material_price_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta(
        "product_raw_material_price_intelligence_10080001.json"
    )
    path = "/products/10080001/raw-material-price-intelligence"
    tables = presenter.build_raw_material_price_intelligence_table_presentations(
        envelope["data"],
        path,
    )
    text = presenter._build_raw_material_price_intelligence_text_presentation(
        envelope["data"],
        path,
    )

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
        explicit_format="kpi",
    )

    assert metadata.get("kpiPresentation", {}).get("type") == "kpi"
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
    assert metadata.get("treePresentation", {}).get("type") == "tree"
    assert metadata.get("dashboardPresentation", {}).get("type") == "dashboard"
    assert "kpi" in (metadata.get("availableFormats") or [])
    assert "chart" in (metadata.get("availableFormats") or [])
    assert "tree" in (metadata.get("availableFormats") or [])
    assert "dashboard" in (metadata.get("availableFormats") or [])
