from tv_app.application.services.data.tv_view_projection_service import (
    aggregate_values,
    apply_field_labels_to_resolved,
    apply_view_projection_to_resolved,
)


def test_aggregate_values_sum_avg_count():
    assert aggregate_values([1, 2, 3], "sum") == 6
    assert aggregate_values([1, 2, 3], "avg") == 2
    assert aggregate_values([1, 2, 3], "count") == 3
    assert aggregate_values([1, 2, 3], "min") == 1
    assert aggregate_values([1, 2, 3], "max") == 3


def test_apply_kpi_projection_aggregates_table_column():
    resolved = {
        "kpiMetrics": [{"field": "oee", "label": "OEE", "value": 80}],
        "table": {
            "columns": [{"key": "oee", "label": "OEE"}],
            "rows": [{"oee": 80}, {"oee": 70}],
        },
    }
    block = {
        "type": "kpi_view",
        "kpiProjection": {
            "metrics": [{"field": "oee", "aggregation": "avg", "label": "OEE médio", "visible": True}]
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["serverProjectionApplied"] is True
    assert next_resolved["kpiMetrics"][0]["value"] == 75
    assert next_resolved["kpi"]["label"] == "OEE médio"


def test_apply_chart_projection_builds_multi_series():
    resolved = {
        "table": {
            "columns": [
                {"key": "periodo", "label": "Período"},
                {"key": "oee", "label": "OEE"},
                {"key": "otd", "label": "OTD"},
            ],
            "rows": [
                {"periodo": "Jan", "oee": 80, "otd": 90},
                {"periodo": "Fev", "oee": 70, "otd": 95},
            ],
        }
    }
    block = {
        "type": "chart_view",
        "chartProjection": {
            "categoryField": "periodo",
            "series": [{"field": "oee", "label": "OEE"}, {"field": "otd", "label": "OTD"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["chart"]["series"][0]["points"][0]["label"] == "Jan"
    assert next_resolved["chart"]["series"][1]["points"][1]["value"] == 95


def test_apply_field_labels_to_resolved_preserves_row_keys():
    resolved = {
        "kpiMetrics": [{"field": "ITEM_CODE", "label": "ITEM_CODE", "value": 1}],
        "table": {
            "columns": [
                {"key": "DETAILED_DESCRIPTION", "label": "DETAILED_DESCRIPTION"},
                {"key": "ITEM_CODE", "label": "ITEM_CODE"},
            ],
            "rows": [{"DETAILED_DESCRIPTION": "x", "ITEM_CODE": "90264019"}],
        },
    }
    next_resolved = apply_field_labels_to_resolved(
        resolved,
        {"DETAILED_DESCRIPTION": "Descrição", "ITEM_CODE": "Código"},
    )
    assert next_resolved["table"]["columns"][0]["label"] == "Descrição"
    assert next_resolved["table"]["columns"][1]["key"] == "ITEM_CODE"
    assert next_resolved["table"]["rows"][0]["ITEM_CODE"] == "90264019"
    assert next_resolved["kpiMetrics"][0]["label"] == "Código"


def test_apply_field_labels_case_insensitive_and_trailing_space():
    resolved = {
        "table": {
            "columns": [{"key": "DETAILED_DESCRIPTION", "label": "DETAILED_DESCRIPTION"}],
            "rows": [{"DETAILED_DESCRIPTION": "x"}],
        },
    }
    next_resolved = apply_field_labels_to_resolved(
        resolved,
        {"detailed_description": "Descrição detalhada "},
    )
    assert next_resolved["table"]["columns"][0]["label"] == "Descrição detalhada "


def test_table_projection_keeps_field_labels_over_auto_baked():
    resolved = {
        "table": {
            "columns": [{"key": "ITEM_CODE", "label": "Código"}],
            "rows": [{"ITEM_CODE": "1"}, {"ITEM_CODE": "2"}],
        },
    }
    block = {
        "type": "table_view",
        "tableProjection": {
            "columns": [{"key": "ITEM_CODE", "label": "ITEM_CODE", "visible": True}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["table"]["columns"][0]["label"] == "Código"
