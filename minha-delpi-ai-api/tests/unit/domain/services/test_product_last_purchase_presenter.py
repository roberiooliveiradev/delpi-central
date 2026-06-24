from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_last_purchase_schema_first_table_columns():
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"
    table = presenter.build_presentation(envelope["data"], path=path)
    keys = [column["key"] for column in table.get("columns") or []]

    assert table.get("type") == "table"
    assert "unit_price" in keys
    assert "icms_rate" in keys
    assert "supplier_name" in keys
