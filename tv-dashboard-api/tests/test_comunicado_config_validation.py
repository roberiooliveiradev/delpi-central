from unittest.mock import MagicMock

import pytest

from tv_app.application.services.comunicado_config_validation_service import (
    max_data_blocks_per_slide,
    sanitize_comunicado_config,
    validate_comunicado_native_config,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def test_sanitize_strips_resolved_and_media_urls():
    cleaned = sanitize_comunicado_config(
        {
            "version": 4,
            "blocks": [
                {
                    "id": "1",
                    "type": "data_kpi",
                    "dataBinding": {"operationId": "get_overall_equipment_effectiveness_pct"},
                    "resolved": {"kpi": {"value": 99}},
                },
                {
                    "id": "2",
                    "type": "image",
                    "assetId": "a",
                    "url": "https://example.com/x.jpg",
                    "frame": {"x": 0, "y": 0, "w": 10, "h": 10},
                },
            ],
            "background": {"type": "image", "assetId": "bg", "url": "https://example.com/bg.jpg"},
        }
    )
    assert "resolved" not in cleaned["blocks"][0]
    assert "url" not in cleaned["blocks"][1]
    assert "url" not in cleaned["background"]


def test_validate_rejects_disallowed_operation():
    cfg = {
        "blocks": [
            {
                "id": "1",
                "type": "data_kpi",
                "dataBinding": {"operationId": "not_allowed"},
            }
        ]
    }
    with pytest.raises(ValueError):
        validate_comunicado_native_config(cfg)


def test_validate_enforces_max_data_blocks(monkeypatch):
    monkeypatch.setattr(
        "tv_app.application.services.comunicado_config_validation_service.max_data_blocks_per_slide",
        lambda: 1,
    )
    cfg = {
        "blocks": [
            {"id": "1", "type": "data_kpi", "dataBinding": {"operationId": "get_overall_equipment_effectiveness_pct"}},
            {"id": "2", "type": "data_chart", "dataBinding": {"operationId": "get_production_oee_series"}},
        ]
    }
    with pytest.raises(ValueError):
        validate_comunicado_native_config(cfg, catalog=TvDataRouteCatalogService())


def test_max_data_blocks_default():
    assert max_data_blocks_per_slide() >= 1
