"""NCs da auditoria imediatamente anterior — indexação por criterion_code + smoke da rota."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from app.domain.services.audit_5s.audit_5s_previous_criterion_nc import (
    build_previous_criterion_ncs_payload,
    index_previous_ncs_by_criterion_code,
)


def _body(response) -> dict:
    return json.loads(response.body.decode())


def test_index_previous_ncs_by_criterion_code_positive_sibling_negative() -> None:
    rows = [
        {"criterion_code": "u01", "id": "nc-1", "status": "open"},
        {"criterion_code": "U01", "id": "nc-dup", "status": "closed"},
        {"criterion_code": "O02", "id": "nc-2", "status": "in_progress"},
        {"criterion_code": "  ", "id": "nc-empty"},
        {"criterion_code": None, "id": "nc-none"},
    ]
    indexed = index_previous_ncs_by_criterion_code(rows)
    assert list(indexed.keys()) == ["U01", "O02"]
    assert indexed["U01"]["id"] == "nc-1"
    assert "nc-empty" not in {row["id"] for row in indexed.values()}


def test_build_payload_without_previous_audit() -> None:
    payload = build_previous_criterion_ncs_payload(previous_audit=None, nc_rows=[])
    assert payload["previous_audit"] is None
    assert payload["by_criterion_code"] == {}
    assert payload["items"] == []


def test_build_payload_with_previous_audit() -> None:
    payload = build_previous_criterion_ncs_payload(
        previous_audit={
            "id": "a-prev",
            "audit_code": "A5S-1",
            "audit_date": "2026-10-01",
            "shift": "TURNO_1",
        },
        nc_rows=[{"criterion_code": "U01", "id": "nc-1", "description": "Lixo"}],
    )
    assert payload["previous_audit"]["id"] == "a-prev"
    assert payload["by_criterion_code"]["U01"]["id"] == "nc-1"
    assert len(payload["items"]) == 1


@patch(
    "app.interface.http.routes.quality.audit_5s_operational_router.build_audit_5s_repository",
)
def test_get_previous_criterion_nonconformities_route_meta(mock_build) -> None:
    from app.interface.http.routes.quality.audit_5s_operational_router import (
        get_audit_previous_criterion_nonconformities,
    )

    mock_repo = MagicMock()
    mock_repo.get_previous_criterion_nonconformities.return_value = {
        "previous_audit": {
            "id": "prev",
            "audit_code": "A5S-9",
            "audit_date": "2026-10-01",
            "shift": "TURNO_1",
        },
        "by_criterion_code": {
            "U01": {
                "id": "nc-1",
                "criterion_code": "U01",
                "description": "Material desnecessário",
                "status": "open",
            }
        },
        "items": [
            {
                "id": "nc-1",
                "criterion_code": "U01",
                "description": "Material desnecessário",
                "status": "open",
            }
        ],
    }
    mock_build.return_value = mock_repo

    response = get_audit_previous_criterion_nonconformities("audit-current")
    payload = _body(response)

    assert payload["success"] is True
    assert (
        payload["meta"]["operationId"]
        == "get_audit_5s_previous_criterion_nonconformities"
    )
    assert payload["data"]["by_criterion_code"]["U01"]["id"] == "nc-1"
    mock_repo.get_previous_criterion_nonconformities.assert_called_once_with(
        "audit-current"
    )
