from app.application.services.product.protheus_field_normalizer import (
    narrow_product_fields,
    normalize_playbook_payload,
    normalize_stock_payload,
    parse_protheus_yes_no,
    protheus_date_to_iso,
)


def test_parse_protheus_yes_no_values() -> None:
    assert parse_protheus_yes_no("SIM") is True
    assert parse_protheus_yes_no("SIM_SC2") is True
    assert parse_protheus_yes_no("NAO") is False
    assert parse_protheus_yes_no(True) is True


def test_protheus_date_to_iso() -> None:
    assert protheus_date_to_iso("20260604") == "2026-06-04"
    assert protheus_date_to_iso("invalid") is None


def test_normalize_playbook_payload_converts_exclusive_raw_material() -> None:
    payload = {
        "items": [{"component_type": "MP", "exclusive_raw_material": "SIM"}],
        "summary": {"pa_production_started": "SIM"},
        "reference_date": "20260604",
    }

    normalized = normalize_playbook_payload(payload, legacy=False)

    assert normalized["items"][0]["exclusive_raw_material"] is True
    assert normalized["items"][0]["exclusive_raw_material_label"] == "Sim"
    assert normalized["summary"]["pa_production_started"] is True
    assert normalized["summary"]["pa_production_started_label"] == "Sim"
    assert normalized["reference_date_iso"] == "2026-06-04"
    assert normalized["reference_date"] == "2026-06-04"


def test_normalize_playbook_payload_legacy_keeps_strings() -> None:
    payload = {
        "items": [{"exclusive_raw_material": "SIM"}],
        "reference_date": "20260604",
    }

    normalized = normalize_playbook_payload(payload, legacy=True)

    assert normalized["items"][0]["exclusive_raw_material"] == "SIM"
    assert "exclusive_raw_material_label" not in normalized["items"][0]
    assert "reference_date_iso" not in normalized


def test_normalize_stock_payload_adds_location_alias() -> None:
    payload = {
        "items": [{"product_code": "90269001", "warehouse": "01"}],
        "page": 1,
        "page_size": 50,
        "total": 1,
    }

    normalized = normalize_stock_payload(payload, legacy=False)

    assert normalized["items"][0]["location"] == "01"


def test_narrow_product_fields_summary_view() -> None:
    product = {
        "code": "90269001",
        "description": "PA",
        "type": "PA",
        "unit": "UN",
        "group_code": "9026",
        "active": "S",
        "blocked": "",
        "default_warehouse": "01",
        "sale_price": 10.0,
        "standard_cost": 8.0,
        "last_purchase_price": 7.0,
        "ncm_ipi_position": "00000000",
        "current_revision": "001",
        "last_revision_date": "20260101",
        "make_or_buy": "F",
        "drawing_code": "IGNORAR",
    }

    narrowed = narrow_product_fields(product, view="summary")

    assert "drawing_code" not in narrowed
    assert narrowed["code"] == "90269001"
    assert len(narrowed) == 15
