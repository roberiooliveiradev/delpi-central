from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from production_pulse_app.application.services.work_center_catalog_service import (
    WorkCenterCatalogService,
)
from production_pulse_app.domain.services.binding_validation_service import BindingValidationError


@pytest.fixture
def mock_gateway():
    gateway = MagicMock()
    gateway.list_work_centers.return_value = {
        "branch": "01",
        "items": [
            {
                "work_center": "CT-53",
                "name": "Usinagem CNC",
                "is_final_inspection": False,
            },
            {
                "work_center": "CT-99",
                "name": "Inspeção final",
                "is_final_inspection": True,
            },
        ],
    }
    return gateway


def test_catalog_maps_items_and_filters_search(mock_gateway):
    service = WorkCenterCatalogService(mock_gateway, cache_ttl_seconds=60)

    all_items = service.list_work_centers(branch="01", authorization="Bearer test")
    assert len(all_items["items"]) == 2
    assert all_items["items"][0]["workCenterCode"] == "CT-53"
    assert all_items["items"][0]["workCenterName"] == "Usinagem CNC"
    assert all_items["items"][0]["isFinalInspection"] is False

    filtered = service.list_work_centers(
        branch="01",
        search="inspe",
        authorization="Bearer test",
    )
    assert len(filtered["items"]) == 1
    assert filtered["items"][0]["workCenterCode"] == "CT-99"


def test_catalog_uses_cache(mock_gateway):
    service = WorkCenterCatalogService(mock_gateway, cache_ttl_seconds=300)

    service.list_work_centers(branch="01", authorization="Bearer test")
    service.list_work_centers(branch="01", authorization="Bearer test")

    mock_gateway.list_work_centers.assert_called_once()


def test_validate_unknown_work_center_raises(mock_gateway):
    service = WorkCenterCatalogService(mock_gateway, cache_ttl_seconds=0)

    with pytest.raises(BindingValidationError) as exc_info:
        service.validate_work_center_code(
            branch="01",
            work_center_code="CT-404",
            authorization="Bearer test",
        )
    assert exc_info.value.code == "work_center_not_in_catalog"


def test_validate_known_work_center_ok(mock_gateway):
    service = WorkCenterCatalogService(mock_gateway, cache_ttl_seconds=0)

    service.validate_work_center_code(
        branch="01",
        work_center_code="ct-53",
        authorization="Bearer test",
    )
