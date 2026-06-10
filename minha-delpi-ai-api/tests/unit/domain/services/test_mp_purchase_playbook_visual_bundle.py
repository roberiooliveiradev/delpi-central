from app.domain.services.chat_presentation_visual_bundle_service import (
    ChatPresentationVisualBundleService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _assert_visual_bundle(metadata: dict) -> None:
    assert metadata.get("kpiPresentation", {}).get("type") == "kpi"
    assert metadata.get("dashboardPresentation", {}).get("type") == "dashboard"
    available = metadata.get("availableFormats") or []
    assert "kpi" in available
    assert "dashboard" in available


def test_last_purchase_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"
    tables = presenter.build_last_purchase_table_presentations(envelope["data"], path)

    assert len(tables) >= 2
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "list" for table in tables)


def test_visual_bundle_enriches_last_purchase_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"
    tables = presenter.build_last_purchase_table_presentations(envelope["data"], path)
    text = presenter._build_last_purchase_text_presentation(envelope["data"], path)

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

    _assert_visual_bundle(metadata)
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
    assert metadata.get("treePresentation", {}).get("type") == "tree"


def test_purchase_price_history_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchase_price_history_10080001.json")
    path = "/products/10080001/purchase-price-history"
    tables = presenter.build_purchase_history_table_presentations(envelope["data"], path)

    assert len(tables) >= 2
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "list" for table in tables)


def test_visual_bundle_enriches_purchase_price_history_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchase_price_history_10080001.json")
    path = "/products/10080001/purchase-price-history"
    tables = presenter.build_purchase_history_table_presentations(envelope["data"], path)
    text = presenter._build_purchase_history_text_presentation(envelope["data"], path)

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

    _assert_visual_bundle(metadata)
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
    assert metadata.get("treePresentation", {}).get("type") == "tree"


def test_purchase_budget_history_fixture_present_by_meta_entity():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchase_budget_history_10080001.json")

    humanized = presenter.present(
        envelope,
        path="/products/10080001/purchase-budget-history",
    )

    assert "orçamento" in humanized.get("titulo", "").lower()


def test_visual_bundle_enriches_purchase_budget_history_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchase_budget_history_10080001.json")
    path = "/products/10080001/purchase-budget-history"
    tables = presenter.build_purchase_history_table_presentations(envelope["data"], path)
    text = presenter._build_purchase_history_text_presentation(envelope["data"], path)

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

    _assert_visual_bundle(metadata)


def test_purchases_table_presentations_assign_stack_roles():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    path = "/products/10080001/purchases"
    tables = presenter.build_purchases_table_presentations(envelope["data"], path)

    assert len(tables) >= 2
    assert tables[0].get("role") == "profile"
    assert any(table.get("role") == "list" for table in tables)


def test_visual_bundle_enriches_purchases_with_auxiliary_slots():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    path = "/products/10080001/purchases"
    tables = presenter.build_purchases_table_presentations(envelope["data"], path)
    text = presenter._build_purchases_text_presentation(envelope["data"], path)

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

    _assert_visual_bundle(metadata)
    assert metadata.get("chartPresentation", {}).get("type") == "chart"
    assert metadata.get("treePresentation", {}).get("type") == "tree"
