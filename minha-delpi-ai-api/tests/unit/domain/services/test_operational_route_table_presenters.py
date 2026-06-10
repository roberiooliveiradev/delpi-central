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

    assert "product_code" in _column_keys(detail)
    assert "exclusive_raw_material_label" in _column_keys(detail)


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
