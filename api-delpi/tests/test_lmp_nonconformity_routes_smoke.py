"""Smoke Nível A — NCs LMP (/engineering/lmps/nonconformities)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

from app.interface.http.routes.engineering.lmp_nonconformity_router import (
    LmpNonconformityBody,
    create_lmp_nonconformity,
    delete_lmp_nonconformity,
    get_lmp_nonconformity,
    list_lmp_nonconformities,
    update_lmp_nonconformity,
)
from tests.support.route_contract_smoke import assert_envelope_meta, body_json

_NC_ID = UUID("22222222-2222-2222-2222-222222222222")

_RECORD = {
    "id": str(_NC_ID),
    "registered_at": "2026-07-27T10:00:00+00:00",
    "sale_number": "123456",
    "branch_code": "01",
    "material_code": "MAT-01",
    "supplier_name": "Fornecedor X",
    "purchase_order": "OC-1",
    "invoice_number": "NF-1",
    "qty_received": 10.0,
    "qty_accepted": 8.0,
    "qty_rejected": 2.0,
    "status": "open",
    "defect_description": "Defeito",
    "corrective_actions": "Ação",
    "technical_opinion": "Parecer",
    "product_codes": ["90001234"],
    "created_by": "user@delpi",
    "updated_by": "user@delpi",
    "created_at": "2026-07-27T10:00:00+00:00",
    "updated_at": "2026-07-27T10:00:00+00:00",
}

_ROUTER = "app.interface.http.routes.engineering.lmp_nonconformity_router"


@patch(f"{_ROUTER}.build_list_lmp_nonconformities_use_case")
def test_list_lmp_nonconformities_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 50,
    }
    mock_build.return_value = use_case

    response = list_lmp_nonconformities()
    assert_envelope_meta(
        body_json(response),
        operation_id="list_lmp_nonconformities",
        shape="paged_list",
    )


@patch(f"{_ROUTER}.build_get_lmp_nonconformity_use_case")
def test_get_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _RECORD
    mock_build.return_value = use_case

    response = get_lmp_nonconformity(record_id=_NC_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="get_lmp_nonconformity",
        shape="scalar",
    )


@patch(f"{_ROUTER}.build_create_lmp_nonconformity_use_case")
def test_create_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _RECORD
    mock_build.return_value = use_case

    response = create_lmp_nonconformity(
        body=LmpNonconformityBody(
            registered_at="2026-07-27T10:00:00+00:00",
            status="open",
            sale_number="123456",
            product_codes=["90001234"],
        )
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="create_lmp_nonconformity",
        shape="scalar",
    )


@patch(f"{_ROUTER}.build_update_lmp_nonconformity_use_case")
def test_update_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = _RECORD
    mock_build.return_value = use_case

    response = update_lmp_nonconformity(
        record_id=_NC_ID,
        body=LmpNonconformityBody(
            registered_at="2026-07-27T10:00:00+00:00",
            status="in_progress",
        ),
    )
    assert_envelope_meta(
        body_json(response),
        operation_id="update_lmp_nonconformity",
        shape="scalar",
    )


@patch(f"{_ROUTER}.build_delete_lmp_nonconformity_use_case")
def test_delete_lmp_nonconformity_returns_meta(mock_build) -> None:
    use_case = MagicMock()
    use_case.execute.return_value = True
    mock_build.return_value = use_case

    response = delete_lmp_nonconformity(record_id=_NC_ID)
    assert_envelope_meta(
        body_json(response),
        operation_id="delete_lmp_nonconformity",
        shape="scalar",
    )
