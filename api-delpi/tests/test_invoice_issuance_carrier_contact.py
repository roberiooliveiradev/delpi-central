from app.domain.services.invoice_issuance.carrier_contact import (
    enrich_request_carrier,
    format_carrier_address,
    format_carrier_phone,
)


def test_format_carrier_address_matches_faturamento_email_shape() -> None:
    text = format_carrier_address(
        street="Rodovia BR-470, 8220",
        district="Canta Galo",
        city="Rio do Sul",
        state="SC",
        zip_code="89163020",
    )
    assert text == "Rodovia BR-470, 8220, Canta Galo, Rio do Sul-SC, CEP 89163-020"


def test_format_carrier_phone_prefixes_ddd() -> None:
    assert format_carrier_phone(ddd="47", phone="3522-6972") == "(47) 3522-6972"
    assert format_carrier_phone(ddd="47", phone="(47) 3522-6972") == "(47) 3522-6972"
    assert format_carrier_phone(ddd="", phone="") is None


def test_enrich_fills_missing_contact_without_overwriting() -> None:
    request = {
        "carrier_code": "000001",
        "carrier_name": "MIR",
        "carrier_address": None,
    }
    live = {
        "carrier_code": "000001",
        "carrier_name": "MIR TRANSP",
        "legal_name": "Mir Transp. Logistica LTDA",
        "tax_id": "03565095000189",
        "address": "Rodovia BR-470, 8220, Canta Galo, Rio do Sul-SC, CEP 89163-020",
        "phone": "(47) 3522-6972",
    }
    out = enrich_request_carrier(request, live)
    assert out["carrier_name"] == "MIR"
    assert out["carrier_legal_name"] == "Mir Transp. Logistica LTDA"
    assert out["carrier_tax_id"] == "03565095000189"
    assert "89163-020" in (out["carrier_address"] or "")
    assert out["carrier_phone"] == "(47) 3522-6972"
