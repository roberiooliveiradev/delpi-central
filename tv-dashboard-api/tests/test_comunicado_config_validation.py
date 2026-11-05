import pytest

from tv_app.application.services.comunicado_config_validation_service import (
    sanitize_comunicado_config,
    validate_comunicado_native_config,
)
from tv_app.application.services.data.tv_data_config_validation_service import (
    TvDataConfigValidationService,
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


def test_sanitize_keeps_chart_authoring_and_drops_runtime_percentage():
    cleaned = sanitize_comunicado_config(
        {
            "version": 4,
            "blocks": [
                {
                    "id": "chart1",
                    "type": "chart_view",
                    "chartType": "pie",
                    "chartOptions": {
                        "decimalPlaces": 2,
                        "displayValueFormat": {"category": "number", "decimalPlaces": 2},
                        "dataLabels": {
                            "showValue": True,
                            "showCategoryName": True,
                            "showPercentage": True,
                            "position": "outsideEnd",
                            "separator": "comma",
                        },
                    },
                    "chartParts": {"marker:0:1": {"visible": False}},
                    "resolved": {
                        "chart": {
                            "points": [
                                {
                                    "label": "A",
                                    "value": 25,
                                    "percentageOfTotal": 25,
                                    "displayPercentageOfTotal": "25,00%",
                                }
                            ]
                        }
                    },
                }
            ],
        }
    )
    block = cleaned["blocks"][0]
    assert "resolved" not in block
    assert block["chartOptions"]["dataLabels"]["showPercentage"] is True
    assert block["chartOptions"]["dataLabels"]["position"] == "outsideEnd"
    assert block["chartOptions"]["dataLabels"]["separator"] == "comma"
    assert block["chartOptions"]["displayValueFormat"]["decimalPlaces"] == 2
    assert block["chartParts"]["marker:0:1"]["visible"] is False
    assert "displayPercentageOfTotal" not in block


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


def test_validate_allows_many_data_blocks():
    """Sem teto artificial de blocos de dados por slide."""
    catalog = TvDataRouteCatalogService()
    cfg = {
        "blocks": [
            {
                "id": str(index),
                "type": "data_kpi",
                "dataBinding": {"operationId": "get_overall_equipment_effectiveness_pct"},
            }
            for index in range(12)
        ]
    }
    result = TvDataConfigValidationService(catalog=catalog).validate(cfg)
    assert not any(
        "Limite de blocos" in str(issue.get("message") or "") for issue in result["issues"]
    )
    assert not any(
        issue.get("field") == "blocks" and "Limite" in str(issue.get("message") or "")
        for issue in result["issues"]
    )
