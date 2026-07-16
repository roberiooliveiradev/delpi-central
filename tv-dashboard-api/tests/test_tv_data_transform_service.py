from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_steps,
    apply_data_transform_to_payload,
    evaluate_safe_arithmetic_expr,
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


def test_apply_to_payload_marks_applied():
    data, applied, table = apply_data_transform_to_payload(
        [{"a": 1, "b": 2}, {"a": 3, "b": 4}],
        {"steps": [{"op": "addColumn", "name": "c", "expr": "a + b"}]},
    )
    assert applied is True
    assert data == [{"a": 1, "b": 2, "c": 3.0}, {"a": 3, "b": 4, "c": 7.0}]
    assert table is not None
