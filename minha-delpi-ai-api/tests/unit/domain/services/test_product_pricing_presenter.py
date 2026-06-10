from app.domain.services.chat_presentation_visual_bundle_service import (
    ChatPresentationVisualBundleService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_present_product_pricing_fixture_by_meta_entity():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_pricing_10080001.json")

    humanized = presenter.present(
        envelope,
        path="/products/10080001/pricing",
    )

    assert "Preço de venda" in humanized.get("titulo", "")
    body = "\n".join(humanized.get("linhas") or [])
    assert "1.25" in body or "Tabela" in body


def test_product_pricing_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_pricing_10080001.json")
    path = "/products/10080001/pricing"
    tables = presenter.build_product_pricing_table_presentations(envelope["data"], path)

    assert len(tables) >= 2
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "list" for table in tables)

    prices = next(table for table in tables if table.get("role") == "list")
    price_keys = [column["key"] for column in prices.get("columns") or []]

    assert "sale_price" in price_keys
    assert "table_description" in price_keys


def test_visual_bundle_enriches_sale_pricing_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_pricing_10080001.json")
    path = "/products/10080001/pricing"
    tables = presenter.build_product_pricing_table_presentations(envelope["data"], path)
    text = presenter._build_product_pricing_text_presentation(envelope["data"], path)

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
