import importlib.util
from pathlib import Path


def _load_module():
    path = Path("scripts/check_operational_action_readiness.py")
    spec = importlib.util.spec_from_file_location("check_operational_action_readiness", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def test_action_matches_by_operation_id():
    module = _load_module()

    assert module._action_matches(
        {"operationId": "get_production_schedule_today", "path": "/production/schedule/today"},
        {"operationId": "get_production_schedule_today", "path": "/other"},
    )


def test_action_matches_by_path_when_operation_id_differs():
    module = _load_module()

    assert module._action_matches(
        {"operationId": "get_production_schedule_today", "path": "/production/schedule/today"},
        {"operationId": "", "path": "/production/schedule/today"},
    )


def test_critical_actions_cover_playbook_15_matrix():
    module = _load_module()

    operation_ids = {item["operationId"] for item in module.CRITICAL_ACTIONS}

    assert operation_ids == {
        "get_production_schedule_today",
        "get_production_orders_open",
        "get_production_consumption_top_items",
        "get_purchases_top_products",
    }
