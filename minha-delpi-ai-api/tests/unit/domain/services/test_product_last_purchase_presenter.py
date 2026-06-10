from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_last_purchase_table_uses_operational_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"
    tables = presenter.build_last_purchase_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "list")
    keys = [column["key"] for column in detail.get("columns") or []]

    assert "unit_price" in keys
    assert "icms_rate" in keys
    assert "supplier_name" in keys
    assert "invoice_number" in keys or "issue_date" in keys
