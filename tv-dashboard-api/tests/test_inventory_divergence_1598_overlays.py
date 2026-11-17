"""TV Dashboard: catálogo amigável dos três blocos do GLPI #1598."""
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TV_OVERLAYS = ROOT / "tv-dashboard-api/tv_app/content/tv_data_route_overlays.json"
API_ROUTER = ROOT / "api-delpi/app/interface/http/routes/supplies/inventory_adjustments_router.py"
CONTRACTS = ROOT / "api-delpi/app/interface/http/route_contract_registry.py"


def _overlay(operation_id):
    payload = json.loads(TV_OVERLAYS.read_text(encoding="utf-8"))
    return payload["overlays"][operation_id]


def test_two_kpis_have_unambiguous_absolute_brl_measures():
    operation_id = "get_supplies_inventory_adjustments_tv_summary"
    overlay = _overlay(operation_id)
    assert "year_divergence_brl" in overlay["valueFields"]
    assert "month_divergence_brl" in overlay["valueFields"]
    assert overlay["valueFieldTypes"]["year_divergence_brl"] == "number"
    assert overlay["allowedDisplayModes"] == ["kpi", "auto"]
    assert "sobras" in overlay["description"].lower()


def test_series_can_be_used_as_a_chart_by_month():
    overlay = _overlay("get_supplies_inventory_adjustments_tv_monthly_series")
    assert overlay["tableFields"] == "items"
    assert "bar_chart" in overlay["allowedDisplayModes"]
    assert "shortage_value_brl" in overlay["valueFields"]
    assert "surplus_value_brl" in overlay["valueFields"]


def test_weekly_top_n_table_includes_code_description_quantity_and_brl():
    overlay = _overlay("get_supplies_inventory_adjustments_tv_weekly_items")
    assert overlay["tableFields"] == "items"
    assert "table" in overlay["allowedDisplayModes"]
    assert overlay["paramSchema"]["top_limit"]["maximum"] == 50
    for field in ("product_code", "product_description", "quantity", "value_brl"):
        assert field in overlay["valueFieldLabels"]


def test_all_three_operation_ids_exist_in_api_contract_and_router():
    contract_source = CONTRACTS.read_text(encoding="utf-8")
    router_source = API_ROUTER.read_text(encoding="utf-8")
    for op in (
        "get_supplies_inventory_adjustments_tv_summary",
        "get_supplies_inventory_adjustments_tv_monthly_series",
        "get_supplies_inventory_adjustments_tv_weekly_items",
    ):
        assert op in contract_source
        assert op in router_source
