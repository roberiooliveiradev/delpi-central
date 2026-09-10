"""E7.S5 — labels/formats schema-first no build path (sem LLM de tipo)."""

from __future__ import annotations

from app.composition.content_composer import configure_domain_infrastructure_ports
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)
from app.domain.services.external_actions.external_action_result_presenter import (
    ExternalActionResultPresenter,
)

configure_domain_infrastructure_ports()


def _currency_schema() -> dict:
    return {
        "200": {
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "items": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "unit_price": {
                                            "type": "number",
                                            "x-dataType": "currency",
                                        },
                                        "qty": {
                                            "type": "number",
                                            "x-dataType": "quantity",
                                        },
                                        "code": {"type": "string"},
                                    },
                                },
                            }
                        },
                    }
                }
            }
        }
    }


def test_e7_s5_schema_currency_beats_missing_field_formats_json():
    """Positive: OpenAPI x-dataType currency → dataType even without fieldFormats entry."""

    service = ExternalActionColumnLabelService()
    schema_formats = service.resolve_schema_formats(_currency_schema())
    assert schema_formats.get("unit_price") == "currency"

    columns = service.resolve_columns_for_items(
        [{"code": "A", "unit_price": 10.5, "qty": 2}],
        path="/ext/acme/prices",
        schema_formats=schema_formats,
    )
    by_key = {col["key"]: col for col in columns}
    assert by_key["unit_price"].get("dataType") == "currency"
    assert by_key["qty"].get("dataType") == "quantity"


def test_e7_s5_build_presentation_wires_schema_formats():
    """Wiring: build_presentation aplica resolve_schema_formats nas colunas."""

    presenter = ExternalActionResultPresenter()
    payload = {
        "items": [
            {"code": "10080001", "unit_price": 12.3, "qty": 1},
        ]
    }
    result = presenter.build_presentation(
        payload,
        path="/ext/acme/prices",
        response_schema=_currency_schema(),
    )
    assert isinstance(result, dict)
    assert result.get("type") == "table"
    columns = result.get("columns") or []
    by_key = {str(col.get("key") or ""): col for col in columns if isinstance(col, dict)}
    assert by_key["unit_price"].get("dataType") == "currency"
    assert by_key["qty"].get("dataType") == "quantity"


def test_e7_s5_meta_field_formats_override_openapi():
    """Sibling: meta.fieldFormats sobrescreve schema OpenAPI no merge."""

    service = ExternalActionColumnLabelService()
    schema_formats = service.resolve_schema_formats(_currency_schema())
    merged = service.merge_meta_field_formats(
        schema_formats,
        {
            "meta": {"fieldFormats": {"unit_price": "quantity"}},
            "items": [{"unit_price": 1}],
        },
    )
    assert merged.get("unit_price") == "quantity"


def test_e7_s5_negative_no_llm_invented_currency_for_neutral_key():
    """Negative: tipagem é schema → fieldFormats → inferência; sem LLM inventando currency."""

    service = ExternalActionColumnLabelService()
    # Chave sem token monetário e sem entry JSON → None (não LLM)
    assert service.resolve_field_format("sku_ref") is None
    assert "R$" not in service.format_field_value("sku_ref", "90269002")
    # Schema explícito tipa sem inventar via modelo
    assert (
        service.resolve_field_format(
            "sku_ref",
            schema_formats={"sku_ref": "quantity"},
        )
        == "quantity"
    )


def test_e7_s5_json_field_formats_remain_fallback():
    """KEEP R07-02: fieldFormats JSON / inferência ainda tipam sem schema."""

    service = ExternalActionColumnLabelService()
    columns = service.resolve_columns_for_items(
        [{"sale_price": 1.2, "code": "X"}],
        path="/products/x/pricing",
        schema_formats={},
    )
    by_key = {col["key"]: col for col in columns}
    assert by_key["sale_price"].get("dataType") == "currency"
