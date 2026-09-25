"""Merge/transform hardening: falhas estruturais devem ser erros tipados.

TRANSFORM FAILURE != EMPTY DATASET
JOIN FAILURE != NO ROWS
BINDING FAILURE != NULL VALUE
"""

import pytest

from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_steps,
    apply_data_transform_to_payload_result,
)
from tv_app.domain.data_query.m_execution import MExecutionError


SOURCE_A = {
    "columns": ["branch", "segment", "rol"],
    "rows": [{"branch": "01", "segment": "weg", "rol": 100}],
}
SOURCE_B = {
    "columns": ["branch", "segment", "rol"],
    "rows": [{"branch": "01", "segment": "weg", "rol": 80}],
}


def _merge_step(**overrides):
    step = {
        "op": "merge",
        "sourceId": "b",
        "leftKey": "join_key",
        "rightKey": "join_key",
        "join": "left",
    }
    step.update(overrides)
    return step


def test_merge_valid_1to1_preserves_left_fields():
    left = {
        "columns": ["branch", "segment", "rol", "join_key"],
        "rows": [{"branch": "01", "segment": "weg", "rol": 100, "join_key": "01|weg"}],
    }
    right = {
        "columns": ["join_key", "rol_prev"],
        "rows": [{"join_key": "01|weg", "rol_prev": 80}],
    }
    out = apply_data_transform_steps(
        left, [_merge_step()], sibling_tables={"b": right}
    )
    assert out["columns"] == ["branch", "segment", "rol", "join_key", "rol_prev"]
    assert out["rows"] == [
        {
            "branch": "01",
            "segment": "weg",
            "rol": 100,
            "join_key": "01|weg",
            "rol_prev": 80,
        }
    ]


def test_merge_missing_left_key_raises_typed_error():
    left = {"columns": ["branch", "rol"], "rows": [{"branch": "01", "rol": 100}]}
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            left, [_merge_step()], sibling_tables={"b": SOURCE_B}
        )
    assert exc.value.code == "m.unknown_column"


def test_merge_missing_right_key_raises_typed_error():
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 100}],
    }
    right = {"columns": ["sku", "rol_prev"], "rows": [{"sku": "01", "rol_prev": 80}]}
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            left, [_merge_step()], sibling_tables={"b": right}
        )
    assert exc.value.code == "m.unknown_column"


def test_merge_missing_source_raises_typed_error():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A, [_merge_step()], sibling_tables={}
        )
    assert exc.value.code == "m.merge_source_unavailable"


def test_merge_duplicate_right_key_raises_cardinality_error():
    right = {
        "columns": ["join_key", "rol_prev"],
        "rows": [
            {"join_key": "01", "rol_prev": 80},
            {"join_key": "01", "rol_prev": 90},
        ],
    }
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 100}],
    }
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            left, [_merge_step()], sibling_tables={"b": right}
        )
    assert exc.value.code == "m.merge_cardinality_violation"


def test_merge_field_collision_raises_error():
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 100}],
    }
    right = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 80}],
    }
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            left, [_merge_step()], sibling_tables={"b": right}
        )
    assert exc.value.code == "m.merge_field_collision"


def test_merge_key_type_mismatch_normalizes_numbers():
    """Normalização explícita: números canonizados (1 == 1.0 == "1" via int->str);
    strings não-numéricas preservadas."""
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "1", "rol": 100}],
    }
    right = {
        "columns": ["join_key", "rol_prev"],
        "rows": [{"join_key": 1, "rol_prev": 80}],
    }
    out = apply_data_transform_steps(
        left, [_merge_step()], sibling_tables={"b": right}
    )
    assert out["rows"][0]["rol_prev"] == 80


def test_merge_zero_matches_raises_typed_error():
    """Ambos os lados não-vazios e nenhum match = join failure, não linhas vazias."""
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 100}],
    }
    right = {
        "columns": ["join_key", "rol_prev"],
        "rows": [{"join_key": "99", "rol_prev": 80}],
    }
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            left, [_merge_step()], sibling_tables={"b": right}
        )
    assert exc.value.code == "m.merge_no_matches"


def test_merge_null_key_never_matches():
    """Chave nula nunca casa (política explícita); linha passa com fill None."""
    left = {
        "columns": ["join_key", "rol"],
        "rows": [
            {"join_key": None, "rol": 100},
            {"join_key": "01", "rol": 200},
        ],
    }
    right = {
        "columns": ["join_key", "rol_prev"],
        "rows": [
            {"join_key": None, "rol_prev": 1},
            {"join_key": "01", "rol_prev": 80},
        ],
    }
    out = apply_data_transform_steps(
        left, [_merge_step()], sibling_tables={"b": right}
    )
    assert out["rows"] == [
        {"join_key": None, "rol": 100, "rol_prev": None},
        {"join_key": "01", "rol": 200, "rol_prev": 80},
    ]


def test_merge_take_columns_must_exist_on_right():
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 100}],
    }
    right = {
        "columns": ["join_key", "rol_prev"],
        "rows": [{"join_key": "01", "rol_prev": 80}],
    }
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            left,
            [_merge_step(columns=["rol_nope"])],
            sibling_tables={"b": right},
        )
    assert exc.value.code == "m.unknown_column"


def test_merge_empty_right_is_valid_empty_result():
    """Dataset vazio genuíno continua sucesso: left passa com fill None."""
    left = {
        "columns": ["join_key", "rol"],
        "rows": [{"join_key": "01", "rol": 100}],
    }
    right = {"columns": ["join_key", "rol_prev"], "rows": []}
    out = apply_data_transform_steps(
        left, [_merge_step()], sibling_tables={"b": right}
    )
    assert out["rows"] == [{"join_key": "01", "rol": 100, "rol_prev": None}]


def test_add_column_overwrite_existing_is_collision():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A,
            [{"op": "addColumn", "name": "rol", "expr": "rol * 2"}],
        )
    assert exc.value.code == "m.column_collision"


def test_add_column_unknown_identifier_is_typed_error():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A,
            [{"op": "addColumn", "name": "x", "expr": "rol_prev * 2"}],
        )
    assert exc.value.code == "m.unknown_column"


def test_select_unknown_column_is_typed_error():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A, [{"op": "select", "columns": ["branch", "nope"]}]
        )
    assert exc.value.code == "m.unknown_column"


def test_rename_unknown_column_is_typed_error():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A, [{"op": "rename", "from": "nope", "to": "x"}]
        )
    assert exc.value.code == "m.unknown_column"


def test_rename_collision_is_typed_error():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A, [{"op": "rename", "from": "rol", "to": "segment"}]
        )
    assert exc.value.code == "m.column_collision"


def test_filter_unknown_column_is_typed_error():
    with pytest.raises(MExecutionError) as exc:
        apply_data_transform_steps(
            SOURCE_A,
            [{"op": "filter", "column": "nope", "cmp": "eq", "value": "x"}],
        )
    assert exc.value.code == "m.unknown_column"


def test_failure_propagates_as_failed_result_not_empty_data():
    """O resultado tipado carrega failed + runtimeErrors (não data=[] silencioso)."""
    result = apply_data_transform_to_payload_result(
        [{"branch": "01", "rol": 100}],
        {"steps": [_merge_step()]},
        sibling_tables={},
    )
    assert result["applied"] is False
    assert result["failed"] is True
    errors = result["runtimeErrors"]
    assert errors["count"] == 1
    assert errors["sample"][0]["code"] == "m.merge_source_unavailable"


def test_valid_transform_still_applies_cleanly():
    result = apply_data_transform_to_payload_result(
        [{"a": 1, "b": 2}],
        {"steps": [{"op": "addColumn", "name": "c", "expr": "a + b"}]},
    )
    assert result["applied"] is True
    assert result["data"] == [{"a": 1, "b": 2, "c": 3.0}]
    assert result["runtimeErrors"]["count"] == 0
