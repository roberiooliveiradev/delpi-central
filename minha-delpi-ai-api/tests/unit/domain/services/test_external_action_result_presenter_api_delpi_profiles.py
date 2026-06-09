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


def test_present_production_status_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "Análise produtiva" in humanized.get("titulo", "")
    assert "NAO" in body or "não" in body.lower() or "Produção" in body


def test_build_presentation_production_status_tables_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_production_status_90269002.json")

    tables = presenter.build_production_status_table_presentations(
        envelope["data"],
        "/products/90269002/production-status",
    )

    assert len(tables) >= 1
    assert tables[0]["type"] == "table"


def test_present_shipping_status_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_shipping_status_90269002.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "Expedição" in humanized.get("titulo", "")
    assert "10" in body or "exped" in body.lower()


def test_build_presentation_shipping_status_tables_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_shipping_status_90269002.json")

    tables = presenter.build_shipping_status_table_presentations(
        envelope["data"],
        "/products/90269002/shipping-status",
    )

    assert len(tables) >= 1
    assert tables[0]["type"] == "table"


def test_present_structure_exclusivity_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90269002.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "exclusividade" in humanized.get("titulo", "").lower()
    assert "10019001" in body or "exclusiv" in body.lower()


def test_build_presentation_structure_exclusivity_tables_from_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_structure_exclusivity_90269002.json")

    tables = presenter.build_structure_exclusivity_table_presentations(
        envelope["data"],
        "/products/90269002/structure/exclusivity",
    )

    assert len(tables) >= 1
    assert tables[0]["type"] == "table"


def test_present_factory_status_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_factory_status_90269002.json")

    humanized = presenter.present(envelope, path="")

    body = "\n".join(humanized.get("linhas") or [])

    assert "OP ABERTA" in body or "Situação consolidada" in body or "fábrica" in body.lower()


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
    assert any(row.get("campo") == "Situação consolidada" for row in table.get("rows") or [])


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


def test_present_dict_fallback_nested_key_placeholder_does_not_crash() -> None:
    """Regressão: placeholder {key} no template não pode colidir com parâmetro text_key."""
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


def test_present_raw_material_price_intelligence_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta(
        "product_raw_material_price_intelligence_10080001.json"
    )

    humanized = presenter.present(
        envelope,
        path="/products/10080001/raw-material-price-intelligence",
    )

    assert "Análise de preço" in humanized.get("titulo", "")
    body = "\n".join(humanized.get("linhas") or [])
    assert "ESTAVEL" in body or "000002" in body


def test_build_presentation_raw_material_price_intelligence_tables() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta(
        "product_raw_material_price_intelligence_10080001.json"
    )

    tables = presenter.build_raw_material_price_intelligence_table_presentations(
        envelope["data"],
        "/products/10080001/raw-material-price-intelligence",
    )

    assert len(tables) >= 2
    assert all(table["type"] == "table" for table in tables)


def test_present_cost_impact_simulation_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_cost_impact_simulation_90261255.json")

    humanized = presenter.present(
        envelope,
        path="/products/90261255/cost-impact-simulation",
    )

    assert "Simulador" in humanized.get("titulo", "")
    body = "\n".join(humanized.get("linhas") or [])
    assert "10080002" in body or "250" in body


def test_present_last_purchase_fixture_by_meta_entity() -> None:
    presenter = ExternalActionResultPresenter()
    envelope = load_api_delpi_fixture_with_meta("product_last_purchase_10080001.json")

    humanized = presenter.present(
        envelope,
        path="/products/10080001/last-purchase",
    )

    assert "Última compra" in humanized.get("titulo", "")
    body = "\n".join(humanized.get("linhas") or [])
    assert "000002" in body or "0.089" in body
