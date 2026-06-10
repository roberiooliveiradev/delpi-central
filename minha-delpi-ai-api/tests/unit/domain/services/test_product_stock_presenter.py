from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import load_api_delpi_fixture_with_meta


def test_stock_highlights_negative_total_and_attention() -> None:
    presenter = ExternalActionResultPresenter()
    items = [
        {
            "product_code": "10080022",
            "branch": "01",
            "warehouse": "01",
            "current_quantity": 10.0,
            "available_quantity": -5.0,
            "committed_quantity": 15.0,
        },
        {
            "product_code": "10080022",
            "branch": "02",
            "warehouse": "01",
            "current_quantity": 0.0,
            "available_quantity": 0.0,
            "committed_quantity": 0.0,
        },
    ]

    humanized = presenter._present_product_stock(
        items,
        path="/products/10080022/stock",
        root={"items": items, "total": 2, "page": 1, "page_size": 50},
    )
    markdown = humanized.get("humanizedMarkdown") or ""

    assert "negativo" in markdown.lower()
    assert "**Destaques**" in markdown
    assert "**Pontos de atenção**" in markdown
    assert "zerado" in markdown.lower() or "zero" in markdown.lower()


def test_stock_table_presentations_use_fixed_position_columns() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")
    path = "/products/90269001/stock"
    tables = presenter.build_stock_table_presentations(envelope["data"], path)
    detail = next(table for table in tables if table.get("role") == "list")
    keys = [column["key"] for column in detail.get("columns") or []]

    assert "branch" in keys
    assert "warehouse" in keys
    assert "available_quantity" in keys
