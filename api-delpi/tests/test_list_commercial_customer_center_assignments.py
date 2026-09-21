"""Smoke — list_commercial_customer_center_assignments."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_REPO = (
    "app.infrastructure.persistence.totvs.commercial_repositories."
    "commercial_customer_center_catalog_repository.CommercialCustomerCenterCatalogRepository"
)


@patch(_REPO)
def test_assignments_keep_1100_and_1200_on_the_same_pair(mock_repo_cls) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        list_commercial_customer_center_assignments,
    )

    repository = MagicMock()
    repository.list_assignments.return_value = [
        {
            "customer_code": "000001",
            "customer_store": "01",
            "center": "1100",
            "label": "WEG MOTORES (1100)",
        },
        {
            "customer_code": "000001",
            "customer_store": "01",
            "center": "1200",
            "label": "WEG MOTORES (1200)",
        },
    ]
    mock_repo_cls.return_value = repository

    response = list_commercial_customer_center_assignments(customer_codes="000001")
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="list_commercial_customer_center_assignments",
        shape="list",
    )
    centers = [item["center"] for item in payload["data"]["items"]]
    assert centers == ["1100", "1200"]
    assert "1700" not in centers
    assert payload["data"]["items"][0]["customer_store"] == "01"
    assert "WEG DRIVES" not in payload["data"]["items"][0]["label"]
    repository.list_assignments.assert_called_once_with(["000001"])
