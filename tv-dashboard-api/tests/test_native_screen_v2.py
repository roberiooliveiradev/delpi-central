from unittest.mock import MagicMock

from tv_app.application.services.native_screen_data_service import NativeScreenDataService
from tv_app.application.services.tv_dashboard_content_service import trend_direction_label


def test_native_catalog_includes_v2_screens():
    catalog = NativeScreenDataService.catalog()
    keys = {item["key"] for item in catalog}
    assert "supplies_stock_alert" in keys
    assert "strategic_indicators_hero" in keys


def test_supplies_stock_alert_resolves_top_products():
    gateway = MagicMock()
    gateway.fetch_stock_alert.return_value = {
        "branch": "01",
        "itemLimit": 6,
        "items": [{"productCode": "10080047", "description": "Item A", "stockValue": 1000}],
        "label": "Itens críticos de estoque",
    }
    service = NativeScreenDataService(gateway=gateway)
    data = service.resolve(
        screen_key="supplies_stock_alert",
        config={"branch": "01", "itemLimit": 6},
    )
    assert data["items"][0]["productCode"] == "10080047"
    gateway.fetch_stock_alert.assert_called_once()


def test_strategic_indicators_hero_resolves():
    gateway = MagicMock()
    strategic = MagicMock()
    strategic.fetch_hero.return_value = {
        "igd": 82.5,
        "classification": "Bom",
        "trendLabel": "Alta",
        "bestDepartment": "Produção",
        "primaryRisk": "Financeiro",
        "label": "Índice Global Delpi",
    }
    service = NativeScreenDataService(gateway=gateway, strategic=strategic)
    data = service.resolve(
        screen_key="strategic_indicators_hero",
        config={"branch": "01", "competence": "2026-05"},
    )
    assert data["igd"] == 82.5
    assert data["bestDepartment"] == "Produção"
    strategic.fetch_hero.assert_called_once()


def test_oee_overview_includes_series_points():
    gateway = MagicMock()
    gateway.fetch_oee_overview.return_value = {
        "oeePct": 75,
        "targetPct": 80,
        "seriesPoints": [{"label": "d1", "value": 70}, {"label": "d2", "value": 75}],
        "label": "OEE",
    }
    service = NativeScreenDataService(gateway=gateway)
    data = service.resolve(screen_key="production_oee_overview", config={"periodDays": 7})
    assert len(data["seriesPoints"]) == 2
    gateway.fetch_oee_overview.assert_called_once()


def test_trend_direction_label_from_content():
    assert trend_direction_label("up") == "Alta"
    assert trend_direction_label("down") == "Queda"
    assert trend_direction_label("stable") == "Estável"
