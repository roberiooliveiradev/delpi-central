from tv_app.application.services.data.tv_view_projection_service import (
    aggregate_values,
    apply_field_labels_to_resolved,
    apply_view_projection_to_resolved,
    resolve_category_display_label,
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
        "chartType": "line",
        "chartProjection": {
            "categoryField": "periodo",
            "series": [{"field": "oee", "label": "OEE"}, {"field": "otd", "label": "OTD"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["chart"]["chartType"] == "line"
    assert next_resolved["chart"]["series"][0]["points"][0]["label"] == "Jan"
    assert next_resolved["chart"]["series"][1]["points"][1]["value"] == 95


def test_apply_chart_projection_doughnut_groups_by_category():
    """Paridade com chartDataPolicy groupByCategory — evita N fatias LMP×1 na TV."""
    resolved = {
        "table": {
            "columns": [{"key": "tipo", "label": "Tipo"}, {"key": "ov", "label": "OV"}],
            "rows": [
                {"tipo": "LMP", "ov": "1"},
                {"tipo": "LMP", "ov": "2"},
                {"tipo": "AMOSTRA", "ov": "3"},
                {"tipo": "LMP", "ov": "4"},
            ],
        }
    }
    block = {
        "type": "chart_view",
        "chartType": "doughnut",
        "chartProjection": {
            "categoryField": "tipo",
            "series": [{"field": "tipo", "aggregation": "count", "label": "Contagem"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    points = next_resolved["chart"]["points"]
    assert next_resolved["chart"]["chartType"] == "doughnut"
    assert len(points) == 2
    by_label = {p["label"]: p["value"] for p in points}
    assert by_label["LMP"] == 3
    assert by_label["AMOSTRA"] == 1


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


def test_resolve_category_display_label_prefers_companion_description():
    assert (
        resolve_category_display_label(
            "FM",
            "code",
            [{"code": "FM", "label": "FM - Falha de material"}],
        )
        == "FM - Falha de material"
    )
    assert (
        resolve_category_display_label(
            "FH",
            "code",
            [{"code": "FH", "label": "Falha humana"}],
        )
        == "FH - Falha humana"
    )


def test_resolve_category_display_label_keeps_product_code_only():
    long_desc = (
        "CABO PP CIRCULAR PVC/PVC 4X1.5MM2 CZ SPT/VDAR 90'C 600V "
        "DIAM EXT 8.20MM VIAS NUMERADAS UL/CSA"
    )
    assert (
        resolve_category_display_label(
            "10070821",
            "code",
            [{"code": "10070821", "label": long_desc}],
        )
        == "10070821"
    )


def test_apply_chart_projection_pie_uses_full_motivo_label():
    resolved = {
        "table": {
            "columns": [
                {"key": "code", "label": "Código"},
                {"key": "label", "label": "Descrição"},
                {"key": "value", "label": "Valor"},
            ],
            "rows": [
                {"code": "FM", "label": "FM - FALHA MECANICA", "value": 102.04},
                {"code": "FH", "label": "FH - FALHA HUMANA", "value": 41.91},
            ],
        }
    }
    block = {
        "type": "chart_view",
        "chartType": "doughnut",
        "chartProjection": {
            "categoryField": "code",
            "series": [{"field": "value", "aggregation": "sum", "label": "Valor"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    labels = [p["label"] for p in next_resolved["chart"]["points"]]
    assert labels == ["FM - FALHA MECANICA", "FH - FALHA HUMANA"]
