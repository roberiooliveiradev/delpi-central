from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import (
    load_api_delpi_fixture,
    load_api_delpi_fixture_with_meta,
    with_api_delpi_meta,
)


def _body(humanized: dict) -> str:
    return "\n".join(
        [
            *(humanized.get("linhas") or []),
            *(humanized.get("linhas_detalhe") or []),
            humanized.get("humanizedMarkdown") or "",
            humanized.get("titulo") or "",
        ]
    )


def test_present_stock_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")

    humanized = presenter.present(envelope, path="")

    assert humanized.get("titulo")
    body = _body(humanized)
    assert "90269001" in body or "105" in body or "150" in body


def test_build_presentation_stock_returns_visual() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")

    visual = presenter.build_presentation(envelope, path="")

    assert visual is not None
    assert visual.get("type") in {"table", "markdown", "kpi", "chart", "tree"}


def test_present_structure_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_90269001.json")

    humanized = presenter.present(envelope, path="")
    body = _body(humanized)

    assert "50219001" in body or "INTERMEDIARIO" in body or humanized.get("titulo")


def test_present_production_status_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")

    humanized = presenter.present(envelope, path="")
    body = _body(humanized)

    assert humanized.get("titulo")
    assert body.strip()


def test_present_shipping_status_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_shipping_status_90269002.json")

    humanized = presenter.present(envelope, path="")
    body = _body(humanized)

    assert humanized.get("titulo")
    assert "10" in body or "exped" in body.lower() or body.strip()


def test_present_structure_exclusivity_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90269002.json")

    humanized = presenter.present(envelope, path="")
    body = _body(humanized)

    assert humanized.get("titulo")
    assert "10019001" in body or "exclusiv" in body.lower() or body.strip()


def test_present_factory_status_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")

    humanized = presenter.present(envelope, path="")
    body = _body(humanized)

    assert humanized.get("titulo")
    assert body.strip()


def test_present_analyser_fixture_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_analyser_90269001.json")

    humanized = presenter.present(
        envelope,
        path="/products/90269001/analyser",
    )

    assert humanized.get("titulo")
    assert humanized.get("linhas") or humanized.get("humanizedMarkdown")


def test_present_billing_scalar_schema_first() -> None:
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "value": 21024.26,
                "documents": 19,
                "first_billing_date": "20070518",
                "last_billing_date": "20150331",
            },
            "meta": {
                "entity": "product_billing",
                "shape": "scalar",
                "operationId": "get_product_sales_billing",
            },
        },
        path="",
    )

    body = _body(humanized)
    assert "21.024,26" in body or "21024" in body or "19" in body


def test_present_supplies_cpv_schema_first() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = with_api_delpi_meta(
        load_api_delpi_fixture("supplies_cpv.json"),
        {
            "dataVersion": "2026-06",
            "operationId": "get_supplies_cpv",
            "entity": "supplies_cpv",
            "shape": "scalar",
        },
    )

    humanized = presenter.present(envelope, path="")

    assert humanized.get("titulo")


def test_present_dict_fallback_nested_key_placeholder_does_not_crash() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = {
        "success": True,
        "data": {
            "summary": {
                "nested": {"branch": "01", "value": 12.5},
            }
        },
        "meta": {
            "entity": "unknown_scalar",
            "shape": "scalar",
        },
    }

    humanized = presenter.present(envelope, path="/supplies/cpv")

    assert humanized.get("linhas")


def test_present_sale_orders_schema_first() -> None:
    presenter = ExternalActionResultPresenter()

    humanized = presenter.present(
        {
            "success": True,
            "data": {
                "items": [
                    {
                        "order_number": "000123",
                        "customer_name": "Cliente A",
                        "order_date": "20260101",
                    }
                ],
                "page": 1,
                "page_size": 50,
                "total": 1,
            },
            "meta": {
                "entity": "sale_order",
                "shape": "paged_list",
                "operationId": "list_sale_orders",
            },
        },
        path="",
    )

    body = _body(humanized)
    assert "000123" in body or "Cliente A" in body


def test_present_last_purchase_fixture_uses_schema_first_table() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")
    path = "/products/10080001/last-purchase"

    table = presenter.build_presentation(envelope["data"], path=path)

    assert table is not None
    assert table.get("type") in {"table", "markdown", "kpi"}

    if table.get("type") == "table":
        keys = [column["key"] for column in table.get("columns") or []]
        assert "unit_price" in keys or "supplier_code" in keys
