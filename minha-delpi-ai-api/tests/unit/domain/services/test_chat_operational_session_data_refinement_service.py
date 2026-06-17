from app.domain.services.chat_operational_session_data_refinement_service import (
    ChatOperationalSessionDataRefinementService,
)


def test_resolve_execution_path_local_for_unit():
    entry = {
        "strategy": "local",
        "localCategoryField": "unit",
        "localMetricFields": ["real_consumption_qty"],
    }
    rows = [
        {"unit": "PC", "real_consumption_qty": 10.0},
        {"unit": "KG", "real_consumption_qty": 5.0},
    ]

    assert ChatOperationalSessionDataRefinementService.resolve_execution_path(entry, rows) == "session"


def test_resolve_execution_path_refetch_for_product_group():
    entry = {
        "strategy": "refetch",
        "refetchGroupBy": "product_group",
    }

    assert (
        ChatOperationalSessionDataRefinementService.resolve_execution_path(
            entry,
            [{"unit": "PC", "real_consumption_qty": 1.0}],
        )
        == "refetch"
    )


def test_resolve_execution_path_auto_prefers_local_when_branch_present():
    entry = {
        "strategy": "auto",
        "localCategoryField": "branch",
        "localMetricFields": ["real_consumption_qty"],
        "refetchGroupBy": "branch_summary",
    }
    rows = [
        {"branch": "01", "real_consumption_qty": 10.0},
        {"branch": "02", "real_consumption_qty": 5.0},
    ]

    assert ChatOperationalSessionDataRefinementService.resolve_execution_path(entry, rows) == "session"
