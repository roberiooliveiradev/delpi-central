"""Regression tests for DelpiCanonicalSupplierReader response-shape handling.

X3.E2E finding: api-delpi `get_protheus_rest_supplier` unwraps the Protheus
REST payload into a flat supplier dict — the reader previously expected a
`fornecedor` wrapper (write contract) and returned None for every supplier.
"""

from unittest.mock import Mock

from app.infrastructure.gateways.delpi_api_gateway import DelpiApiGatewayError
from app.infrastructure.gateways.supplier_enrichment_adapters import (
    DelpiCanonicalSupplierReader,
)


def _reader(payload=None, error=None):
    gateway = Mock()
    if error is not None:
        gateway.get.side_effect = error
    else:
        gateway.get.return_value = payload
    return DelpiCanonicalSupplierReader(gateway=gateway)


FLAT_SUPPLIER = {
    "success": True,
    "data": {
        "supplier_code": "002469",
        "supplier_store": "01",
        "tax_id": "52614426000139",
        "person_type": "J",
        "supplier_name": "RODRIGUES KANNENBERG",
        "supplier_short_name": "RODRIGUES KANNENBERG",
        "address": "RUA EXEMPLO",
        "district": "CENTRO",
        "postal_code": "95700000",
        "state": "RS",
        "city": "BENTO GONCALVES",
        "city_code": "02105",
        "area_code": "54",
        "phone": "34550000",
        "email": "compras@example.com",
    },
}

WRAPPED_SUPPLIER = {
    "success": True,
    "data": {
        "fornecedor": {
            "supplier_code": "003878",
            "supplier_store": "01",
            "tax_id": "98887766000134",
            "person_type": "J",
            "supplier_name": "ZZ HOMOLOG",
        }
    },
}


def test_read_flat_envelope_maps_canonical_snapshot():
    snap = _reader(FLAT_SUPPLIER).read("002469", "01", access_token="u")

    assert snap is not None
    assert snap.supplier.code == "002469"
    assert snap.supplier.store == "01"
    assert snap.tax_id == "52614426000139"
    assert snap.person_type == "J"
    assert snap.fields["supplier_name"] == "RODRIGUES KANNENBERG"
    assert snap.fields["postal_code"] == "95700000"
    assert snap.fields["city_code"] == "02105"


def test_read_wrapped_fornecedor_shape_still_supported():
    snap = _reader(WRAPPED_SUPPLIER).read("003878", "01", access_token="u")

    assert snap is not None
    assert snap.tax_id == "98887766000134"
    assert snap.fields["supplier_name"] == "ZZ HOMOLOG"


def test_read_returns_none_for_empty_payload():
    assert _reader({"success": True, "data": {}}).read(
        "000000", "01", access_token="u"
    ) is None


def test_read_maps_gateway_404_to_none():
    err = DelpiApiGatewayError("not found", status_code=404)
    assert _reader(error=err).read("000000", "01", access_token="u") is None


def test_read_propagates_non_404_gateway_errors():
    err = DelpiApiGatewayError("upstream down", status_code=503)
    try:
        _reader(error=err).read("000000", "01", access_token="u")
    except DelpiApiGatewayError as exc:
        assert exc.status_code == 503
    else:  # pragma: no cover - defensive
        raise AssertionError("expected DelpiApiGatewayError")
