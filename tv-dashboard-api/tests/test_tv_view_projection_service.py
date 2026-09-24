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


def test_apply_kpi_projection_multi_metrics_resolve_distinct_fields():
    """Multi-KPI must not reuse the primary scalar for every metric field."""
    resolved = {
        "kpi": {"value": 4364622.79, "label": "ROL"},
        "kpiMetrics": [
            {"field": "rol", "label": "ROL", "value": 4364622.79},
            {"field": "goal", "label": "Meta", "value": 4364622.79},  # stale shared
            {"field": "attainment", "label": "Atingimento", "value": 4364622.79},
        ],
        "table": {
            "columns": [
                {"key": "rol", "label": "ROL"},
                {"key": "goal", "label": "Meta"},
                {"key": "attainment", "label": "Atingimento"},
            ],
            "rows": [{"rol": 4364622.79, "goal": 5000000.0, "attainment": 87.3}],
        },
    }
    block = {
        "type": "kpi_view",
        "kpiProjection": {
            "metrics": [
                {"field": "rol", "aggregation": "first", "label": "ROL", "visible": True},
                {"field": "goal", "aggregation": "first", "label": "Meta", "visible": True},
                {
                    "field": "attainment",
                    "aggregation": "first",
                    "label": "Atingimento",
                    "visible": True,
                },
            ]
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    by_field = {m["field"]: m["value"] for m in next_resolved["kpiMetrics"]}
    assert by_field["rol"] == 4364622.79
    assert by_field["goal"] == 5000000.0
    assert by_field["attainment"] == 87.3


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




def test_apply_chart_projection_pie_uses_category_column_as_is():
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
    assert labels == ["FM", "FH"]


def test_chart_projection_empty_rows_clears_summary_chart():
    resolved = {
        "chart": {
            "points": [
                {"label": "Buckets quantidade", "value": 5},
                {"label": "Customers quantidade", "value": 0},
            ],
            "chartType": "bar",
        },
        "table": {"columns": [], "rows": []},
    }
    block = {
        "type": "chart_view",
        "chartType": "bar",
        "chartProjection": {
            "categoryField": "periodo",
            "series": [{"field": "total_qty", "label": "Quantidade total", "aggregation": "sum"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["chart"]["points"] == []
    assert next_resolved["chart"]["series"] == []
    assert next_resolved["serverProjectionApplied"] is True


def test_chart_projection_rejects_metric_dump_and_uses_lead_by_level():
    """FE-BE-003: category=nivel + avg_lead_time must not paint kpiMetrics Meta/Total*."""
    resolved = {
        "chart": {
            "points": [
                {"label": "Meta cadastrada", "value": 10},
                {"label": "Meta mês (referência)", "value": 8},
                {"label": "Total itens", "value": 100},
                {"label": "Total lmps", "value": 40},
                {"label": "Média lead time", "value": 3.2},
            ],
            "chartType": "bar",
        },
        "kpiMetrics": [
            {"field": "goal_value", "label": "Meta cadastrada", "value": 10},
            {"field": "reference_goal", "label": "Meta mês (referência)", "value": 8},
            {"field": "total_items", "label": "Total itens", "value": 100},
            {"field": "total_lmps", "label": "Total lmps", "value": 40},
            {"field": "avg_lead_time", "label": "Média lead time", "value": 3.2},
        ],
        "table": {
            "columns": [
                {"key": "metric", "label": "Indicador"},
                {"key": "field", "label": "Campo"},
                {"key": "value", "label": "Valor"},
            ],
            "rows": [
                {"metric": "Meta cadastrada", "field": "goal_value", "value": 10},
                {"metric": "Total itens", "field": "total_items", "value": 100},
                {"metric": "Média lead time", "field": "avg_lead_time", "value": 3.2},
            ],
        },
        "data": {
            "leadByLevel": [
                {"nivel": "Nível 1", "avg_lead_time": 2.5},
                {"nivel": "Nível 2", "avg_lead_time": 4.1},
            ]
        },
    }
    block = {
        "type": "chart_view",
        "chartType": "pie",
        "chartProjection": {
            "categoryField": "nivel",
            "series": [{"field": "avg_lead_time", "aggregation": "avg", "label": "Média lead time"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    labels = [p["label"] for p in next_resolved["chart"]["points"]]
    assert labels == ["Nível 1", "Nível 2"]
    assert {p["label"] for p in next_resolved["chart"]["points"]} == {"Nível 1", "Nível 2"}
    assert "Meta cadastrada" not in labels
    assert "Total itens" not in labels
    assert next_resolved["chart"]["series"][0]["field"] == "avg_lead_time"
    assert next_resolved["serverProjectionApplied"] is True


def test_chart_projection_selected_metrics_only_without_category():
    resolved = {
        "chart": {
            "points": [
                {"label": "Meta cadastrada", "value": 10},
                {"label": "Total itens", "value": 100},
                {"label": "Média lead time", "value": 3.2},
            ],
            "chartType": "bar",
        },
        "kpiMetrics": [
            {"field": "goal_value", "label": "Meta cadastrada", "value": 10},
            {"field": "total_items", "label": "Total itens", "value": 100},
            {"field": "avg_lead_time", "label": "Média lead time", "value": 3.2},
        ],
        "table": {
            "columns": [
                {"key": "metric", "label": "Indicador"},
                {"key": "field", "label": "Campo"},
                {"key": "value", "label": "Valor"},
            ],
            "rows": [
                {"metric": "Meta cadastrada", "field": "goal_value", "value": 10},
                {"metric": "Total itens", "field": "total_items", "value": 100},
            ],
        },
    }
    block = {
        "type": "chart_view",
        "chartType": "bar",
        "chartProjection": {
            "series": [{"field": "avg_lead_time", "label": "Média lead time"}],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert len(next_resolved["chart"]["points"]) == 1
    assert next_resolved["chart"]["points"][0]["value"] == 3.2
    assert next_resolved["chart"]["series"][0]["field"] == "avg_lead_time"
    labels = [p["label"] for p in next_resolved["chart"]["points"]]
    assert "Meta cadastrada" not in labels
    assert "Total itens" not in labels


def test_chart_projection_category_as_measure_falls_back_to_selected_metrics():
    """Scalar ROL summary: categoryField=rol must not leave Sem dados."""
    resolved = {
        "kpiMetrics": [
            {"field": "rol", "label": "ROL", "value": 4364622.79},
            {"field": "comparable_goal", "label": "Meta do período", "value": 5000000.0},
            {"field": "rol_target_pct", "label": "Atingimento", "value": 87.3},
        ],
        # KPI source suppresses field/value dump — no columnar table.
        "table": {"columns": [], "rows": []},
    }
    block = {
        "type": "chart_view",
        "chartType": "bar",
        "chartProjection": {
            "categoryField": "rol",
            "series": [
                {"field": "comparable_goal", "aggregation": "sum", "label": "Meta do período"},
                {"field": "rol_target_pct", "aggregation": "sum", "label": "Atingimento"},
            ],
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    fields = [s["field"] for s in next_resolved["chart"]["series"]]
    assert fields == ["comparable_goal", "rol_target_pct"]
    assert next_resolved["chart"]["series"][0]["points"][0]["value"] == 5000000.0
    assert next_resolved["serverProjectionApplied"] is True


def test_table_projection_synthesizes_wide_row_from_kpi_metrics():
    """Scalar source without table rows → one wide row for selected measure columns."""
    resolved = {
        "kpiMetrics": [
            {"field": "rol", "label": "ROL", "value": 4364622.79},
            {"field": "comparable_goal", "label": "Meta do período", "value": 5000000.0},
            {"field": "discounts", "label": "Descontos", "value": 100.0},
        ],
        "table": {"columns": [], "rows": []},
    }
    block = {
        "type": "table_view",
        "tableProjection": {
            "columns": [
                {"key": "rol", "label": "ROL", "visible": True},
                {"key": "comparable_goal", "label": "Meta do período", "visible": True},
                {"key": "discounts", "label": "Descontos", "visible": True},
            ]
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert len(next_resolved["table"]["rows"]) == 1
    assert next_resolved["table"]["rows"][0]["rol"] == 4364622.79
    assert next_resolved["table"]["rows"][0]["comparable_goal"] == 5000000.0
    assert next_resolved["table"]["rows"][0]["discounts"] == 100.0
    assert next_resolved["serverProjectionApplied"] is True


def test_table_projection_metric_dump_with_measure_keys_uses_kpi_metrics():
    resolved = {
        "kpiMetrics": [
            {"field": "rol", "label": "ROL", "value": 10},
            {"field": "target", "label": "Meta", "value": 20},
        ],
        "table": {
            "columns": [
                {"key": "metric", "label": "Indicador"},
                {"key": "field", "label": "Campo"},
                {"key": "value", "label": "Valor"},
            ],
            "rows": [
                {"metric": "ROL", "field": "rol", "value": 10},
                {"metric": "Meta", "field": "target", "value": 20},
            ],
        },
    }
    block = {
        "type": "table_view",
        "tableProjection": {
            "columns": [
                {"key": "rol", "visible": True},
                {"key": "target", "visible": True},
            ]
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["table"]["rows"] == [{"rol": 10, "target": 20}]


def test_exclude_weekends_baked_into_chart_points():
    resolved = {
        "viewFilterParams": {"excludeWeekends": True, "granularity": "day"},
        "chart": {
            "chartType": "line",
            "points": [
                {"label": "2024-01-05", "value": 1},  # Friday
                {"label": "2024-01-06", "value": 2},  # Saturday
                {"label": "2024-01-07", "value": 3},  # Sunday
                {"label": "2024-01-08", "value": 4},  # Monday
            ],
        },
        "table": {"columns": [], "rows": []},
    }
    block = {"type": "chart_view", "chartType": "line"}
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    labels = [p["label"] for p in next_resolved["chart"]["points"]]
    assert labels == ["2024-01-05", "2024-01-08"]
    assert next_resolved["serverProjectionApplied"] is True


def test_max_categories_collapses_to_outros():
    rows = [{"cat": f"c{i}", "v": i} for i in range(10)]
    resolved = {
        "table": {
            "columns": [{"key": "cat", "label": "Cat"}, {"key": "v", "label": "V"}],
            "rows": rows,
        }
    }
    block = {
        "type": "chart_view",
        "chartType": "pie",
        "chartProjection": {
            "categoryField": "cat",
            "series": [{"field": "v", "aggregation": "sum", "label": "V"}],
            "maxCategories": 3,
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    labels = [p["label"] for p in next_resolved["chart"]["points"]]
    assert "Outros" in labels
    assert len(labels) == 3


def test_projected_goal_baked():
    resolved = {
        "table": {
            "columns": [{"key": "v", "label": "V"}, {"key": "meta", "label": "Meta"}],
            "rows": [{"v": 10, "meta": 100}, {"v": 20, "meta": 100}],
        }
    }
    block = {
        "type": "chart_view",
        "chartType": "bar",
        "chartProjection": {
            "categoryField": "v",
            "series": [{"field": "v", "aggregation": "sum", "label": "V"}],
            "goalField": "meta",
            "goalAggregation": "first",
        },
    }
    next_resolved = apply_view_projection_to_resolved(resolved, block)
    assert next_resolved["chart"]["projectedGoal"] == 100.0
