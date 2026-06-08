from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)
from tests.fixtures.api_delpi_responses_loader import (
    load_api_delpi_fixture,
    load_api_delpi_fixture_with_meta,
    with_api_delpi_meta,
)


def test_present_stock_fixture_routes_by_meta_without_stock_path() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")

    humanized = presenter.present(envelope, path="")

    assert humanized.get("titulo")
    body = "\n".join(
        [*(humanized.get("linhas") or []), *(humanized.get("linhas_detalhe") or [])]
    )
    assert "105" in body or "150" in body or "filial" in body.lower()


def test_present_structure_fixture_routes_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_90269001.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "50219001" in body or "INTERMEDIARIO" in body


def test_present_factory_status_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "OP ABERTA" in body or "Status fabril" in body


def test_build_presentation_stock_table_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_stock_90269001.json")

    table = presenter.build_presentation(envelope, path="")

    assert table is not None
    assert table["type"] == "table"
    assert len(table.get("rows") or []) >= 1


def test_build_presentation_factory_status_table_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")

    table = presenter.build_presentation(envelope, path="")

    assert table is not None
    assert table["type"] == "table"
    assert any(row.get("campo") == "Status fabril" for row in table.get("rows") or [])


def test_present_analyser_fixture_still_works_with_meta() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_analyser_90269001.json")

    humanized = presenter.present(
        envelope,
        path="/products/90269001/analyser",
    )

    assert humanized.get("titulo")
    assert humanized.get("linhas")


def test_present_billing_routes_by_meta_entity_without_path() -> None:
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

    assert any("21.024,26" in line for line in humanized.get("linhas") or [])


def test_present_supplies_cpv_routes_by_meta_entity_without_path() -> None:
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

    assert "CPV" in humanized.get("titulo", "")


def test_present_sale_orders_routes_by_meta_entity_without_path() -> None:
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

    body = "\n".join(humanized.get("linhas") or [])
    assert "000123" in body or "Cliente A" in body


def test_build_presentation_billing_table_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()

    table = presenter.build_presentation(
        {
            "success": True,
            "data": {
                "value": 21024.26,
                "documents": 19,
            },
            "meta": {
                "entity": "product_billing",
                "shape": "scalar",
                "operationId": "get_product_sales_billing",
            },
        },
        path="",
    )

    assert table is not None
    assert table["type"] == "table"
