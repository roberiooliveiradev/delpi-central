"""Smoke — list_commercial_customer_centers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from tests.support.route_contract_smoke import assert_envelope_meta, body_json


_REPO = (
    "app.infrastructure.persistence.totvs.commercial_repositories."
    "commercial_customer_center_catalog_repository.CommercialCustomerCenterCatalogRepository"
)


@patch(_REPO)
def test_list_commercial_customer_centers_returns_items(mock_repo_cls) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        list_commercial_customer_centers,
    )

    repository = MagicMock()
    repository.list_centers.return_value = [
        {"center": "1100", "label": "WEG MOTORES (1100)"},
        {"center": "1200", "label": "WEG MOTORES (1200)"},
        {"center": "1320", "label": "WEG AUTOMACAO (1320)"},
    ]
    mock_repo_cls.return_value = repository

    response = list_commercial_customer_centers(customer_codes="000001")
    payload = body_json(response)
    assert_envelope_meta(
        payload,
        operation_id="list_commercial_customer_centers",
        shape="list",
    )
    centers = [item["center"] for item in payload["data"]["items"]]
    assert centers == ["1100", "1200", "1320"]
    assert "1700" not in centers
    assert "WEG DRIVES" not in payload["data"]["items"][2]["label"]
    repository.list_centers.assert_called_once_with(["000001"])


@patch(_REPO)
def test_list_commercial_customer_centers_omits_filter_when_blank(mock_repo_cls) -> None:
    from app.interface.http.routes.commercial.commercial_router import (
        list_commercial_customer_centers,
    )

    repository = MagicMock()
    repository.list_centers.return_value = []
    mock_repo_cls.return_value = repository

    response = list_commercial_customer_centers(customer_codes=None)
    payload = body_json(response)
    assert payload["success"] is True
    repository.list_centers.assert_called_once_with(None)
