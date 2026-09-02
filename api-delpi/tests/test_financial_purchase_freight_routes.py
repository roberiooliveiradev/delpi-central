from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.application.use_cases.financial.get_purchase_freight_links_use_case import (
    DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_ITEM = {
    "branch": "01",
    "in_filter": True,
    "link_entry_date": "2026-01-07",
    "invoice_found": True,
    "invoice_document": "000123456",
    "invoice_series": "1",
    "supplier_code": "001992",
    "supplier_store": "03",
    "supplier_name": "FORNECEDOR X",
    "invoice_goods_value": 1000.0,
    "invoice_issue_date": "2026-01-05",
    "invoice_entry_date": "2026-01-07",
    "freight_found": True,
    "freight_document": "000000789",
    "freight_series": "1",
    "carrier_code": "003686",
    "carrier_store": "01",
    "carrier_name": "TRANSPORTADORA Y",
    "freight_gross_value": 32.5,
    "freight_issue_date": "2026-01-06",
    "freight_access_key": "4326" + "0" * 40,
    "freight_document_type": "N",
    "freight_document_kind": "CTE",
}


def _use_case_result() -> dict:
    return {
        "branch": "01",
        "items": [_ITEM],
        "pagination": {
            "limit": DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
            "offset": 0,
            "returned": 1,
            "is_complete": True,
        },
        "summary": {
            "total_records": 1,
            "in_filter_records": 1,
            "branch": "01",
            "branch_filter_applied": True,
            "issue_start": "2026-01-01",
            "issue_end": "2026-01-31",
            "entry_start": "",
            "entry_end": "",
        },
    }


def _call(mock_build, **overrides):
    import app.interface.http.routes.financial.financial_routes as router_mod

    use_case = MagicMock()
    use_case.execute.return_value = _use_case_result()
    mock_build.return_value = use_case

    kwargs = {
        "branch": "01",
        "issue_start": "2026-01-01",
        "issue_end": "2026-01-31",
        "entry_start": None,
        "entry_end": None,
        "supplier": None,
        "invoice_document": None,
        "freight_document": None,
        "limit": DEFAULT_PURCHASE_FREIGHT_LINK_LIMIT,
    }
    kwargs.update(overrides)
    return router_mod.get_financial_purchase_freight_links(**kwargs), use_case


@patch(
    "app.interface.http.routes.financial.financial_routes"
    ".build_get_purchase_freight_links_use_case"
)
def test_get_financial_purchase_freight_links_route_contract(mock_build) -> None:
    response, _ = _call(mock_build)
    payload = body_json(response)

    assert_envelope_meta(
        payload,
        operation_id="get_financial_purchase_freight_links",
        shape="paged_list",
        entity="financial_purchase_freight_link",
    )
    assert payload["data"]["items"][0]["invoice_document"] == "000123456"
    assert payload["data"]["pagination"]["is_complete"] is True


@patch(
    "app.interface.http.routes.financial.financial_routes"
    ".build_get_purchase_freight_links_use_case"
)
def test_route_exposes_freight_field_labels(mock_build) -> None:
    response, _ = _call(mock_build)
    fields = body_json(response)["meta"]["fields"]

    assert fields["invoice_goods_value"] == "Valor da mercadoria"
    assert fields["freight_gross_value"] == "Valor bruto do CT-e"
    assert fields["in_filter"] == "Atende ao filtro"


@patch(
    "app.interface.http.routes.financial.financial_routes"
    ".build_get_purchase_freight_links_use_case"
)
def test_route_forwards_every_filter_to_the_use_case(mock_build) -> None:
    _, use_case = _call(
        mock_build,
        entry_start="2026-02-01",
        entry_end="2026-02-28",
        supplier="001992",
        invoice_document="000123456",
        freight_document="000000789",
    )

    request = use_case.execute.call_args.args[0]
    assert request.branch == "01"
    assert request.issue_start == "2026-01-01"
    assert request.entry_end == "2026-02-28"
    assert request.supplier == "001992"
    assert request.invoice_document == "000123456"
    assert request.freight_document == "000000789"
