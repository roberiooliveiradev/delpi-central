"""Parameter ExpressionSpec — loader, fase, avaliação e integração de merge."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from tv_app.application.services.comunicado_data_params_service import merge_data_params
from tv_app.application.services.data.m_query.m_expression_interpreter import (
    MExpressionError,
)
from tv_app.application.services.data.value_expression_service import (
    ExpressionPhase,
    build_evaluation_context,
    compile_expression_spec,
    is_expression_value,
    params_contain_expressions,
    resolve_param_expressions,
    assert_no_unresolved_expressions,
    validate_expression_param_value,
)
from tv_app.domain.data_query.transform_plan import CompiledExpression


ROUTE = {
    "operationId": "op_test",
    "path": "/sales/realized",
    "httpMethod": "GET",
    "paramStrategy": "date_range",
    "paramSchema": {
        "start_date": {"type": "string", "format": "date", "optional": False},
        "end_date": {"type": "string", "format": "date", "optional": False},
        "periodDays": {"type": "integer", "optional": True},
        "branch": {"type": "string", "enum": ["01", "02", "all"], "optional": True},
        "ratio": {"type": "number", "optional": True},
        "slug": {"type": "string", "in": "path", "optional": False},
        "current": {"type": "number", "optional": True},
        "previous": {"type": "number", "optional": True},
    },
}


def _lit(value):
    return {"kind": "literal", "value": value}


def _ident(name):
    return {"kind": "identifier", "value": name}


def _call(name, *children):
    return {"kind": "call", "value": name, "children": list(children)}


def _bin(op, left, right):
    return {"kind": "binary", "value": op, "children": [left, right]}


def _spec(ast, *, version=1):
    return {"expression": {"version": version, "expression": ast}}


def _ctx(today: date):
    return build_evaluation_context(today=today, now=datetime(today.year, today.month, today.day))


FIXED = _ctx(date(2026, 9, 29))


# --------------------------------------------------------------------- loader


def test_loader_round_trip():
    ast = _call("Date.StartOfMonth", _ident("today"))
    node = CompiledExpression.from_dict(ast)
    assert node.kind == "call"
    assert node.value == "Date.AddMonths" or node.value == "Date.StartOfMonth"
    assert node.to_dict()["kind"] == "call"


def test_loader_rejects_unknown_kind():
    with pytest.raises(Exception):
        CompiledExpression.from_dict({"kind": "exec", "value": "os.system"})


def test_loader_rejects_extra_keys():
    with pytest.raises(Exception):
        CompiledExpression.from_dict({"kind": "literal", "value": 1, "evil": True})


def test_loader_rejects_non_scalar_literal():
    with pytest.raises(Exception):
        CompiledExpression.from_dict({"kind": "literal", "value": {"a": 1}})


def test_loader_rejects_bad_binary_op():
    with pytest.raises(Exception):
        CompiledExpression.from_dict(_bin("**", _lit(1), _lit(2)))


def test_loader_enforces_children_arity():
    with pytest.raises(Exception):
        CompiledExpression.from_dict({"kind": "if", "children": [_lit(True)]})


def test_loader_depth_limit():
    node: dict = _lit(1)
    for _ in range(45):
        node = {"kind": "unary", "value": "+", "children": [node]}
    with pytest.raises(Exception):
        CompiledExpression.from_dict(node, max_depth=40)


def test_loader_node_limit():
    node = {"kind": "list", "children": [_lit(i) for i in range(300)]}
    with pytest.raises(Exception):
        CompiledExpression.from_dict(node, max_nodes=256)


def test_loader_string_size_limit():
    with pytest.raises(Exception):
            CompiledExpression.from_dict(_lit("x" * 600), max_string_bytes=512)


# ------------------------------------------------------- phase / ref control


def test_phase_parameter_forbids_field_ref():
    spec = _spec({"kind": "field", "value": "rol"})
    with pytest.raises(MExpressionError) as exc:
        compile_expression_spec(
            spec,
            phase=ExpressionPhase.PARAMETER,
            allowed_identifiers=frozenset({"today", "now"}),
        )
    assert exc.value.code == "m.expression_reference_not_allowed"


def test_phase_parameter_forbids_unknown_identifier():
    spec = _spec(_ident("secret_env_var"))
    with pytest.raises(MExpressionError) as exc:
        compile_expression_spec(
            spec,
            phase=ExpressionPhase.PARAMETER,
            allowed_identifiers=frozenset({"today", "now"}),
        )
    assert exc.value.code == "m.expression_reference_not_allowed"


def test_phase_parameter_forbids_table_function():
    spec = _spec(_call("Table.SelectColumns", _ident("Fonte"), _lit("x")))
    with pytest.raises(MExpressionError) as exc:
        compile_expression_spec(
            spec,
            phase=ExpressionPhase.PARAMETER,
            allowed_identifiers=frozenset({"today", "now", "param.x"}),
        )
    assert exc.value.code == "m.expression_operator_not_allowed"


def test_phase_parameter_arity_checked_against_registry():
    spec = _spec(_call("Date.AddMonths", _ident("today")))
    with pytest.raises(MExpressionError) as exc:
        compile_expression_spec(
            spec,
            phase=ExpressionPhase.PARAMETER,
            allowed_identifiers=frozenset({"today"}),
        )
    assert exc.value.code == "m.expression_schema_invalid"


def test_spec_version_rejected():
    with pytest.raises(MExpressionError) as exc:
        compile_expression_spec(
            _spec(_lit(1), version=99),
            phase=ExpressionPhase.PARAMETER,
            allowed_identifiers=frozenset({"today"}),
        )
    assert exc.value.code == "m.expression_schema_invalid"


# ------------------------------------------------------------ date evaluation


def _resolve(params):
    return resolve_param_expressions(params, route=ROUTE, context=FIXED)


def test_current_month_to_date_fixed_clock():
    merged = {
        "start_date": _spec(_call("Date.StartOfMonth", _ident("today"))),
        "end_date": _spec(_ident("today")),
    }
    result = _resolve(merged)
    assert result.error is None
    assert result.params["start_date"] == "2026-09-01"
    assert result.params["end_date"] == "2026-09-29"
    assert len(result.trace) == 2
    assert result.trace[0]["resolved"] == "2026-09-01"


def test_same_month_previous_year_to_same_day():
    shifted = _call("Date.AddMonths", _ident("today"), _lit(-12))
    merged = {
        "start_date": _spec(_call("Date.StartOfMonth", shifted)),
        "end_date": _spec(shifted),
    }
    result = _resolve(merged)
    assert result.error is None
    assert result.params["start_date"] == "2025-09-01"
    assert result.params["end_date"] == "2025-09-29"


def test_current_year_to_date():
    merged = {
        "start_date": _spec(_call("Date.StartOfYear", _ident("today"))),
        "end_date": _spec(_ident("today")),
    }
    result = _resolve(merged)
    assert result.error is None
    assert result.params["start_date"] == "2026-01-01"
    assert result.params["end_date"] == "2026-09-29"


def test_same_period_previous_year():
    shifted = _call("Date.AddMonths", _ident("today"), _lit(-12))
    merged = {
        "start_date": _spec(_call("Date.StartOfYear", shifted)),
        "end_date": _spec(shifted),
    }
    result = _resolve(merged)
    assert result.error is None
    assert result.params["start_date"] == "2025-01-01"
    assert result.params["end_date"] == "2025-09-29"


def test_expressions_adapt_to_different_clock():
    other = _ctx(date(2026, 10, 7))
    shifted = _call("Date.AddMonths", _ident("today"), _lit(-12))
    merged = {
        "start_date": _spec(_call("Date.StartOfMonth", shifted)),
        "end_date": _spec(shifted),
    }
    result = resolve_param_expressions(merged, route=ROUTE, context=other)
    assert result.error is None
    assert result.params["start_date"] == "2025-10-01"
    assert result.params["end_date"] == "2025-10-07"


def test_leap_day_shift_clamps():
    leap = _ctx(date(2024, 2, 29))
    merged = {
        "end_date": _spec(_call("Date.AddMonths", _ident("today"), _lit(-12))),
    }
    result = resolve_param_expressions(merged, route=ROUTE, context=leap)
    assert result.error is None
    assert result.params["end_date"] == "2023-02-28"


# ------------------------------------------------------------------- numeric


def test_numeric_generic_composition():
    merged = {
        "current": 120,
        "previous": 100,
        "ratio": _spec(
            _bin(
                "*",
                _bin(
                    "-",
                    _bin("/", _ident("param.current"), _ident("param.previous")),
                    _lit(1),
                ),
                _lit(100),
            )
        ),
    }
    result = _resolve(merged)
    assert result.error is None
    assert result.params["ratio"] == pytest.approx(20)


def test_division_by_zero_typed_error():
    merged = {
        "previous": 0,
        "ratio": _spec(_bin("/", _lit(1), _ident("param.previous"))),
    }
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] == "m.division_by_zero"
    assert result.error["param"] == "ratio"


def test_null_result_typed_error():
    merged = {"branch": _spec({"kind": "literal"})}
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] == "m.expression_null_result"


def test_type_mismatch_date_param():
    merged = {"start_date": _spec(_bin("+", _lit(1), _lit(2)))}
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] in {"m.expression_type_mismatch", "m.date_conversion"}


def test_enum_mismatch():
    merged = {"branch": _spec(_lit("99"))}
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] == "m.expression_type_mismatch"


def test_enum_accepted():
    merged = {"branch": _spec(_lit("01"))}
    result = _resolve(merged)
    assert result.error is None
    assert result.params["branch"] == "01"


def test_integer_param_requires_integral():
    merged = {"periodDays": _spec(_bin("/", _lit(7), _lit(2)))}
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] == "m.expression_type_mismatch"
    merged_ok = {"periodDays": _spec(_bin("/", _lit(6), _lit(2)))}
    result_ok = _resolve(merged_ok)
    assert result_ok.error is None
    assert result_ok.params["periodDays"] == 3


# ------------------------------------------------------------ param gating


def test_expression_on_unknown_param_rejected():
    merged = {"not_a_schema_param": _spec(_lit("x"))}
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] == "m.expression_param_not_allowed"


def test_expression_on_path_param_rejected():
    merged = {"slug": _spec(_lit("abc"))}
    result = _resolve(merged)
    assert result.error is not None
    assert result.error["code"] == "m.expression_param_not_allowed"


def test_validate_expression_param_value_rejects_bad_spec():
    with pytest.raises(MExpressionError):
        validate_expression_param_value("start_date", {"expression": {"version": 2}}, route=ROUTE)


# --------------------------------------------------------------- merge order


def test_expression_layer_overrides_lower_literal():
    merged = merge_data_params(
        playlist_defaults={"end_date": "2020-01-01"},
        slide_filters={"end_date": _spec(_ident("today"))},
        block_params={"start_date": "2020-01-01"},
        input_overrides=None,
    )
    result = _resolve(merged)
    assert result.error is None
    assert result.params["end_date"] == "2026-09-29"
    assert result.params["start_date"] == "2020-01-01"


def test_literal_layer_overrides_lower_expression():
    merged = merge_data_params(
        playlist_defaults={"end_date": _spec(_ident("today"))},
        slide_filters={"end_date": "2021-05-05"},
        block_params={},
        input_overrides=None,
    )
    result = _resolve(merged)
    assert result.error is None
    assert result.params["end_date"] == "2021-05-05"


def test_expression_period_intent_is_atomic():
    # Par start+end por expressão = datas fechadas: preset relativo de camada
    # inferior é removido no merge (mesma regra de datas literais).
    merged = merge_data_params(
        playlist_defaults={"dateRangePreset": "this_year"},
        slide_filters={},
        block_params={
            "start_date": _spec(_call("Date.StartOfMonth", _ident("today"))),
            "end_date": _spec(_ident("today")),
        },
        input_overrides=None,
    )
    assert merged.get("dateRangePreset") in (None, "")
    result = _resolve(merged)
    assert result.error is None
    assert result.params["start_date"] == "2026-09-01"
    assert result.params["end_date"] == "2026-09-29"


# ----------------------------------------------------------- gateway defense


def test_unresolved_expression_never_reaches_wire():
    with pytest.raises(MExpressionError) as exc:
        assert_no_unresolved_expressions({"start_date": _spec(_ident("today"))})
    assert exc.value.code == "m.expression_unresolved"


def test_marker_detection():
    assert is_expression_value(_spec(_lit(1)))
    assert not is_expression_value({"expression": "text"})
    assert not is_expression_value("2026-01-01")
    assert params_contain_expressions({"a": 1}, {"b": _spec(_lit(1))})
    assert not params_contain_expressions({"a": 1}, {"b": 2})
