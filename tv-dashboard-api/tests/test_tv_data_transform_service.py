from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_steps,
    apply_data_transform_to_payload,
    evaluate_safe_arithmetic_expr,
    evaluate_safe_column_expr,
    normalize_data_transform,
)


def test_normalize_data_transform_keeps_known_ops():
    normalized = normalize_data_transform(
        {
            "steps": [
                {"op": "rename", "from": "oee", "to": "oee_pct"},
                {"op": "nope"},
                {"op": "filter", "column": "branch", "cmp": "eq", "value": "01"},
            ]
        }
    )
    assert normalized == {
        "steps": [
            {"op": "rename", "from": "oee", "to": "oee_pct"},
            {"op": "filter", "column": "branch", "cmp": "eq", "value": "01"},
        ]
    }


def test_apply_steps_round_trip_like_ts():
    table = {
        "columns": ["oee", "meta", "branch"],
        "rows": [
            {"oee": 80, "meta": 85, "branch": "01"},
            {"oee": 90, "meta": 85, "branch": "02"},
            {"oee": None, "meta": 85, "branch": "03"},
        ],
    }
    next_table = apply_data_transform_steps(
        table,
        [
            {"op": "rename", "from": "oee", "to": "oee_pct"},
            {"op": "filter", "column": "branch", "cmp": "neq", "value": "03"},
            {"op": "addColumn", "name": "gap", "expr": "meta - oee_pct"},
            {"op": "select", "columns": ["branch", "gap"]},
        ],
    )
    assert next_table["columns"] == ["branch", "gap"]
    assert next_table["rows"] == [
        {"branch": "01", "gap": 5.0},
        {"branch": "02", "gap": -5.0},
    ]


def test_safe_expr_rejects_calls():
    assert evaluate_safe_arithmetic_expr("oee + meta", {"oee": 1, "meta": 2}) == 3.0
    assert evaluate_safe_arithmetic_expr("oee + evil()", {"oee": 1}) is None


def test_column_expr_dsl():
    assert evaluate_safe_column_expr('if(oee >= meta, "ok", "nok")', {"oee": 90, "meta": 85}) == "ok"
    assert evaluate_safe_column_expr('concat("F", branch)', {"branch": "01"}) == "F01"
    assert evaluate_safe_column_expr("coalesce(gap, 0)", {"gap": None}) == 0
    assert evaluate_safe_column_expr("abs(meta - oee)", {"meta": 85, "oee": 90}) == 5.0
    assert evaluate_safe_column_expr("lower(trim(name))", {"name": "  AB "}) == "ab"


def test_apply_to_payload_marks_applied():
    data, applied, table = apply_data_transform_to_payload(
        [{"a": 1, "b": 2}, {"a": 3, "b": 4}],
        {"steps": [{"op": "addColumn", "name": "c", "expr": "a + b"}]},
    )
    assert applied is True
    assert data == [{"a": 1, "b": 2, "c": 3.0}, {"a": 3, "b": 4, "c": 7.0}]
    assert table is not None


def test_group_by_sort_replace():
    next_table = apply_data_transform_steps(
        {
            "columns": ["branch", "oee"],
            "rows": [
                {"branch": "01", "oee": 80},
                {"branch": "01", "oee": 90},
                {"branch": "02", "oee": 70},
            ],
        },
        [
            {"op": "replace", "column": "branch", "find": "0", "replaceWith": "F"},
            {
                "op": "groupBy",
                "keys": ["branch"],
                "aggregations": [{"column": "oee", "fn": "sum", "as": "oee_sum"}],
            },
            {"op": "sort", "column": "oee_sum", "direction": "desc"},
        ],
    )
    assert next_table["rows"] == [
        {"branch": "F1", "oee_sum": 170.0},
        {"branch": "F2", "oee_sum": 70.0},
    ]


def test_pivot_unpivot():
    pivoted = apply_data_transform_steps(
        {
            "columns": ["periodo", "filial", "oee"],
            "rows": [
                {"periodo": "2024-01", "filial": "01", "oee": 80},
                {"periodo": "2024-01", "filial": "02", "oee": 90},
            ],
        },
        [{"op": "pivot", "column": "filial", "valueColumn": "oee", "aggregation": "sum"}],
    )
    assert pivoted["columns"] == ["periodo", "_01", "_02"]
    assert pivoted["rows"] == [{"periodo": "2024-01", "_01": 80.0, "_02": 90.0}]

    back = apply_data_transform_steps(
        pivoted,
        [
            {
                "op": "unpivot",
                "columns": ["_01", "_02"],
                "nameColumn": "filial",
                "valueColumn": "oee",
            }
        ],
    )
    assert back["rows"] == [
        {"periodo": "2024-01", "filial": "_01", "oee": 80.0},
        {"periodo": "2024-01", "filial": "_02", "oee": 90.0},
    ]


def test_merge_with_sibling_tables():
    left = {
        "columns": ["code", "qty"],
        "rows": [{"code": "A", "qty": 1}, {"code": "B", "qty": 2}],
    }
    right = {
        "columns": ["sku", "name"],
        "rows": [{"sku": "A", "name": "Alpha"}, {"sku": "B", "name": "Beta"}],
    }
    next_table = apply_data_transform_steps(
        left,
        [
            {
                "op": "merge",
                "sourceId": "other",
                "leftKey": "code",
                "rightKey": "sku",
                "join": "left",
            }
        ],
        sibling_tables={"other": right},
    )
    assert next_table["rows"] == [
        {"code": "A", "qty": 1, "name": "Alpha"},
        {"code": "B", "qty": 2, "name": "Beta"},
    ]


def test_keep_rows_fill_down_change_type():
    next_table = apply_data_transform_steps(
        {
            "columns": ["g", "v"],
            "rows": [
                {"g": "x", "v": "1"},
                {"g": None, "v": "2"},
                {"g": "y", "v": "3"},
            ],
        },
        [
            {"op": "fillDown", "column": "g"},
            {"op": "changeType", "column": "v", "to": "number"},
            {"op": "keepRows", "count": 2, "from": "top"},
        ],
    )
    assert next_table["rows"] == [
        {"g": "x", "v": 1.0},
        {"g": "x", "v": 2.0},
    ]
