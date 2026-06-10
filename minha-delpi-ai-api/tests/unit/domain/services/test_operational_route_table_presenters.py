from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def _column_keys(table: dict) -> list[str]:
    return [column["key"] for column in table.get("columns") or [] if column.get("key")]


def test_production_status_table_uses_operational_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")
    path = "/products/90269002/production-status"
    tables = presenter.build_production_status_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "list")

    assert "production_order" in _column_keys(detail)
    assert "order_quantity" in _column_keys(detail)
    assert "reported_quantity" in _column_keys(detail)


def test_shipping_status_table_uses_operational_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_shipping_status_90269002.json")
    path = "/products/90269002/shipping-status"
    tables = presenter.build_shipping_status_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "list")

    assert "shipped_quantity" in _column_keys(detail)
    assert "work_center" in _column_keys(detail)


def test_structure_exclusivity_table_uses_operational_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90269002.json")
    path = "/products/90269002/structure/exclusivity"
    tables = presenter.build_structure_exclusivity_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "structure")

    assert "component_code" in _column_keys(detail)
    assert "exclusive_raw_material_label" in _column_keys(detail)


def test_structure_exclusivity_tree_nests_flat_bom_items():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90261805.json")
    path = "/products/90261805/structure/exclusivity"
    tree = presenter.build_structure_exclusivity_tree_presentation(envelope["data"], path)

    assert tree is not None
    assert tree["type"] == "tree"

    root = tree["root"]
    assert len(root.get("children") or []) == 1

    pi = root["children"][0]
    assert "50222613" in pi["label"]
    assert len(pi.get("children") or []) == 2


def test_structure_exclusivity_text_includes_shared_mp_conclusion():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90261805.json")
    path = "/products/90261805/structure/exclusivity"
    text = presenter._build_structure_exclusivity_text_presentation(envelope["data"], path)

    assert text is not None
    markdown = text["markdown"]

    assert "10020053" in markdown
    assert "10" in markdown
    assert "10080185" in markdown
    assert "24" in markdown
    assert "exclusiva" in markdown.lower()


def test_stock_table_uses_product_position_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    path = "/products/90269001/stock"
    tables = presenter.build_stock_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "list")

    assert "product_code" in _column_keys(detail)
    assert "available_quantity" in _column_keys(detail)


def test_purchases_table_uses_purchase_order_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_purchases_10080001.json")
    path = "/products/10080001/purchases"
    tables = presenter.build_purchases_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "list")

    assert "order_number" in _column_keys(detail)
    assert "supplier_name" in _column_keys(detail)
