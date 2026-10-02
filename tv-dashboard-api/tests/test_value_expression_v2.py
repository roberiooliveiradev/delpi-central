"""TV-DATA-EXPR-002 — expressões tipadas v2.

Cobre: registry 1.4.0 tipado, novas funções (Date/Number/Text/List/Value/Logic),
lazy semantics, typecheck estático, weekday enum, precedência preset↔expression
e o caso motivador (semana que contém o 1º do mês, sem datas futuras).
"""

from __future__ import annotations

from datetime import date, datetime

import pytest

from tv_app.application.services.comunicado_data_params_service import (
    merge_data_params,
)
from tv_app.application.services.data.m_query.m_expression_interpreter import (
    MExpressionError,
    _LAZY_FUNCTIONS,
    evaluate_compiled_expression,
)
from tv_app.application.services.data.m_query.m_function_registry import (
    get_function_registry,
)
from tv_app.application.services.data.value_expression_service import (
    ExpressionPhase,
    assert_no_unresolved_expressions,
    build_evaluation_context,
    compile_expression_spec,
    expression_capability,
    resolve_param_expressions,
    validate_expression_param_value,
)
from tv_app.application.services.tv_date_range_preset_service import (
    apply_date_range_preset,
)
from tv_app.domain.data_query.transform_plan import CompiledExpression


ROUTE = {
    "operationId": "op_atendimento_weekly",
    "path": "/atendimento/weekly",
    "httpMethod": "GET",
    "paramStrategy": "date_range",
    "dateRangeKeys": ["start_date", "end_date"],
    "paramSchema": {
        "start_date": {"type": "string", "format": "date", "optional": False},
        "end_date": {"type": "string", "format": "date", "optional": False},
        "granularity": {"type": "string", "enum": ["week", "month"], "optional": True},
        "ratio": {"type": "number", "optional": True},
        "slug": {"type": "string", "in": "path", "optional": False},
        "locked": {"type": "string", "expressionAllowed": False, "optional": True},
    },
}


def _lit(value):
    return {"kind": "literal", "value": value}


def _ident(name):
    return {"kind": "identifier", "value": name}


def _call(name, *children):
    return {"kind": "call", "value": name, "children": list(children)}


def _spec(ast):
    return {"expression": {"version": 1, "expression": ast}}


def _ctx(today: date):
    return build_evaluation_context(
        today=today, now=datetime(today.year, today.month, today.day, 12, 0, 0)
    )


def _eval(ast, *, today=date(2026, 10, 2)):
    ctx = _ctx(today)
    node = CompiledExpression.from_dict(ast)
    return evaluate_compiled_expression(
        node,
        environment={"today": ctx.today, "now": ctx.now},
        culture=ctx.culture,
    )


MOTIVATING_START = _call(
    "Date.StartOfWeek",
    _call("Date.StartOfMonth", _ident("today")),
    _ident("Monday"),
)
MOTIVATING_END = _ident("today")


# ------------------------------------------------------- caso motivador (RQ1)


def test_motivating_atendimento_weekly_october_2026():
    """2026-10-02 (sex): mês começa qui 10-01 → semana inicia seg 09-28; fim=hoje."""
    out = resolve_param_expressions(
        {
            "start_date": _spec(MOTIVATING_START),
            "end_date": _spec(MOTIVATING_END),
            "granularity": "week",
        },
        route=ROUTE,
        context=_ctx(date(2026, 10, 2)),
    )
    assert out.error is None
    assert out.params["start_date"] == "2026-09-28"
    assert out.params["end_date"] == "2026-10-02"
    assert out.params["granularity"] == "week"
    # Wire: sem ExpressionSpec e sem preset.
    assert_no_unresolved_expressions(out.params)
    assert "dateRangePreset" not in out.params
    # Trace tipado para preview/diagnóstico.
    by_param = {entry["param"]: entry for entry in out.trace}
    assert by_param["start_date"]["resolved"] == "2026-09-28"
    assert by_param["end_date"]["resolved"] == "2026-10-02"


def test_motivating_rollover_next_day():
    """Sábado 10-03: mesmo AST → janela rola para incluir o dia seguinte."""
    out = resolve_param_expressions(
        {"start_date": _spec(MOTIVATING_START), "end_date": _spec(MOTIVATING_END)},
        route=ROUTE,
        context=_ctx(date(2026, 10, 3)),
    )
    assert out.params["start_date"] == "2026-09-28"
    assert out.params["end_date"] == "2026-10-03"


def test_motivating_rollover_next_month():
    """Novembro: 11-01 é domingo → semana começa seg 10-26."""
    out = resolve_param_expressions(
        {"start_date": _spec(MOTIVATING_START), "end_date": _spec(MOTIVATING_END)},
        route=ROUTE,
        context=_ctx(date(2026, 11, 4)),
    )
    assert out.params["start_date"] == "2026-10-26"
    assert out.params["end_date"] == "2026-11-04"


# ------------------------------------------------------------- Date functions


def test_date_start_end_of_week_sunday_anchor():
    assert _eval(
        _call("Date.StartOfWeek", _lit("2026-10-01"), _ident("Sunday"))
    ) == date(2026, 9, 27)
    assert _eval(
        _call("Date.EndOfWeek", _lit("2026-10-01"), _ident("Monday"))
    ) == date(2026, 10, 4)


def test_date_day_of_week_and_add_weeks():
    # 2026-10-01 é quinta → 3 com âncora Monday.
    assert _eval(_call("Date.DayOfWeek", _lit("2026-10-01"), _ident("Monday"))) == 3
    assert _eval(_call("Date.AddWeeks", _lit("2026-10-01"), _lit(2))) == date(
        2026, 10, 15
    )


def test_date_week_of_year_iso():
    # 2026-01-01 é quinta → ISO week 1; 2025-12-29 (seg) → ISO 2026-W01? Não: 2025-W53.
    assert _eval(_call("Date.WeekOfYear", _lit("2026-01-01"))) == 1


def test_date_add_years_leap_safe():
    assert _eval(_call("Date.AddYears", _lit("2024-02-29"), _lit(1))) == date(
        2025, 2, 28
    )
    assert _eval(_call("Date.AddYears", _lit("2026-10-02"), _lit(-1))) == date(
        2025, 10, 2
    )


def test_date_days_in_month_and_start_end_of_day():
    assert _eval(_call("Date.DaysInMonth", _lit("2026-02-10"))) == 28
    start = _eval(_call("Date.StartOfDay", _lit("2026-10-02")))
    assert isinstance(start, datetime) and (start.hour, start.minute) == (0, 0)
    end = _eval(_call("Date.EndOfDay", _lit("2026-10-02")))
    assert isinstance(end, datetime) and end.hour == 23 and end.minute == 59


def test_date_min_max_between():
    assert _eval(_call("Date.Min", _lit("2026-10-02"), _lit("2026-09-28"))) == date(
        2026, 9, 28
    )
    assert _eval(_call("Date.Max", _lit("2026-10-02"), _lit("2026-09-28"))) == date(
        2026, 10, 2
    )
    assert _eval(
        _call("Date.Between", _lit("2026-10-02"), _lit("2026-09-28"), _ident("today"))
    ) is True
    assert _eval(
        _call("Date.Between", _lit("2026-10-05"), _lit("2026-09-28"), _ident("today"))
    ) is False


# ----------------------------------------------------- null / condicional lazy


def test_value_is_null_coalesce_null_if():
    assert _eval(_call("Value.IsNull", _lit(None))) is True
    assert _eval(_call("Value.IsNull", _lit(0))) is False
    assert _eval(_call("Value.Coalesce", _lit(None), _lit(None), _lit(7))) == 7
    assert _eval(_call("Value.NullIf", _lit("x"), _lit("x"))) is None
    assert _eval(_call("Value.NullIf", _lit("x"), _lit("y"))) == "x"


def test_logic_switch_and_ifs():
    assert _eval(
        _call("Logic.Switch", _lit("b"), _lit("a"), _lit(1), _lit("b"), _lit(2), _lit(9))
    ) == 2
    assert _eval(
        _call("Logic.Ifs", _lit(False), _lit(1), _lit(True), _lit(2), _lit(9))
    ) == 2


def test_lazy_semantics_dead_branch_never_evaluated():
    """Ramo morto com erro (divisão por zero / identificador inexistente) não falha."""
    bad = {"kind": "binary", "value": "/", "children": [_lit(1), _lit(0)]}
    # Coalesce: primeiro não-nulo vence — o terceiro arg nunca é avaliado.
    assert _eval(_call("Value.Coalesce", _lit(None), _lit(5), bad)) == 5
    # Ifs: condição falsa → ramo de resultado com erro não avaliado.
    assert _eval(_call("Logic.Ifs", _lit(False), bad, _lit(True), _lit(3))) == 3
    # Switch: caso não selecionado não é avaliado.
    assert _eval(
        _call("Logic.Switch", _lit("x"), _lit("y"), bad, _lit("x"), _lit(4))
    ) == 4


def test_lazy_parity_registry_vs_interpreter():
    """Registry (lazyArgs) e interpreter (_LAZY_FUNCTIONS) não podem divergir."""
    registry = get_function_registry()
    declared_lazy = {
        name for name, spec in registry.functions.items() if spec.lazy_args
    }
    assert declared_lazy == set(_LAZY_FUNCTIONS)


# ---------------------------------------------------------------------- number


def test_number_min_max_clamp_safedivide():
    assert _eval(_call("Number.Min", _lit(3), _lit(1), _lit(2))) == 1
    assert _eval(_call("Number.Max", _lit(3), _lit(1), _lit(2))) == 3
    assert _eval(_call("Number.Clamp", _lit(15), _lit(0), _lit(10))) == 10
    assert _eval(_call("Number.SafeDivide", _lit(10), _lit(0), _lit(-1))) == -1
    assert _eval(_call("Number.SafeDivide", _lit(10), _lit(4), _lit(-1))) == 2.5


# ------------------------------------------------------------------------ text


def test_text_new_functions():
    assert _eval(_call("Text.Substring", _lit("delpi"), _lit(1), _lit(3))) == "elp"
    assert _eval(_call("Text.Split", _lit("a,b,c"), _lit(","))) == ["a", "b", "c"]
    assert _eval(_call("Text.PadStart", _lit("7"), _lit(3), _lit("0"))) == "007"
    assert _eval(_call("Text.IsNullOrEmpty", _lit(""))) is True
    assert _eval(_call("Text.IsNullOrEmpty", _lit(None))) is True
    assert _eval(_call("Text.EqualsIgnoreCase", _lit("ABC"), _lit("abc"))) is True


# ------------------------------------------------------------------------ list


def test_list_membership_functions():
    lst = {"kind": "list", "children": [_lit("a"), _lit("b"), _lit("a")]}
    assert _eval(_call("List.Contains", lst, _lit("b"))) is True
    assert _eval(_call("List.Distinct", lst)) == ["a", "b"]
    assert _eval(_call("List.Nth", lst, _lit(1))) == "b"
    assert _eval(_call("List.Nth", lst, _lit(9), _lit("fb"))) == "fb"
    assert _eval(_call("List.First", lst)) == "a"
    assert _eval(_call("List.Last", lst)) == "a"
    assert _eval(_call("List.Count", lst)) == 3


# -------------------------------------------------------------- typecheck estático


def _compile(ast, param="start_date"):
    return compile_expression_spec(
        _spec(ast),
        phase=ExpressionPhase.PARAMETER,
        allowed_identifiers=frozenset(
            {"today", "now", "Monday", "Sunday", "param.ratio"}
        ),
        identifier_types={
            "today": "date",
            "now": "datetime",
            "Monday": "weekday",
            "Sunday": "weekday",
            "param.ratio": "number",
        },
        expected_type="date",
        param_name=param,
    )


def test_typecheck_rejects_wrong_argument_type():
    with pytest.raises(MExpressionError) as exc:
        _compile(_call("Date.AddWeeks", _ident("today"), _lit("texto")))
    assert exc.value.code == "expression.type_mismatch"
    assert exc.value.details.get("function") == "Date.AddWeeks"
    assert exc.value.expression_path.endswith("children[1]")


def test_typecheck_rejects_bad_output_type():
    with pytest.raises(MExpressionError) as exc:
        _compile(_call("Text.Upper", _lit("abc")))
    assert exc.value.code in {
        "expression.type_mismatch",
        "expression.output_type_mismatch",
    }


def test_typecheck_rejects_arity():
    with pytest.raises(MExpressionError) as exc:
        _compile(_call("Date.Between", _ident("today"), _ident("today")))
    # Arity é pego pelo gate de fase (_walk_phase) ou pelo typecheck — ambos
    # falham antes de qualquer avaliação.
    assert exc.value.code in {
        "m.expression_schema_invalid",
        "expression.arity_mismatch",
    }


def test_typecheck_accepts_motivating_expression():
    node = _compile(MOTIVATING_START)
    assert node.kind == "call"


def test_weekday_identifier_accepted_and_typed():
    node = _compile(
        _call("Date.StartOfWeek", _ident("today"), _ident("Monday"))
    )
    assert node.kind == "call"


def test_validate_rejects_invalid_before_persist():
    with pytest.raises(MExpressionError):
        validate_expression_param_value(
            "start_date",
            _spec(_call("Date.AddWeeks", _ident("today"), _lit("NaN"))),
            route=ROUTE,
        )


def test_resolve_fails_closed_with_structured_error():
    out = resolve_param_expressions(
        {"start_date": _spec(_call("Date.AddWeeks", _ident("today"), _lit("x")))},
        route=ROUTE,
        context=_ctx(date(2026, 10, 2)),
    )
    assert out.error is not None
    assert out.error["code"] in {
        "expression.type_mismatch",
        "m.expression_type_mismatch",
    }
    assert out.error["param"] == "start_date"
    # Falha pré-fetch: o caller não deve chamar a rota quando error != None.


# --------------------------------------------------- precedência preset↔expr


def test_expression_side_overrides_preset_default_end_filled():
    """{preset this_month, start_date: expr} → start do expr, end do preset."""
    merged = merge_data_params(
        playlist_defaults={"dateRangePreset": "this_month"},
        slide_filters={},
        block_params={"start_date": _spec(MOTIVATING_START)},
        input_overrides={},
    )
    out = resolve_param_expressions(
        merged, route=ROUTE, context=_ctx(date(2026, 10, 2))
    )
    assert out.error is None
    assert out.params["start_date"] == "2026-09-28"  # expressão vence
    assert out.params["end_date"] == "2026-10-02"  # this_month→hoje (default)
    assert "dateRangePreset" not in out.params
    wire = apply_date_range_preset(
        out.params,
        schema_keys=ROUTE["paramSchema"],
        date_range_keys=ROUTE["dateRangeKeys"],
        strategy="date_range",
        today=date(2026, 10, 2),
    )
    assert wire["start_date"] == "2026-09-28"
    assert wire["end_date"] == "2026-10-02"


def test_expression_pair_fully_overrides_preset():
    """start+end expressions → preset totalmente sobreposto e removido."""
    out = resolve_param_expressions(
        {
            "dateRangePreset": "this_year",
            "start_date": _spec(MOTIVATING_START),
            "end_date": _spec(MOTIVATING_END),
        },
        route=ROUTE,
        context=_ctx(date(2026, 10, 2)),
    )
    assert out.params["start_date"] == "2026-09-28"
    assert out.params["end_date"] == "2026-10-02"
    assert "dateRangePreset" not in out.params


def test_preset_alone_still_materializes_stale_literal_defense():
    """Sem expressão: literal ao lado de preset continua stale (defesa)."""
    out = apply_date_range_preset(
        {
            "dateRangePreset": "this_month",
            "start_date": "2026-09-01",
            "end_date": "2026-09-24",
        },
        schema_keys=ROUTE["paramSchema"],
        strategy="date_range",
        today=date(2026, 10, 2),
    )
    assert out["start_date"] == "2026-10-01"
    assert out["end_date"] == "2026-10-02"


def test_persistence_normalization_keeps_expression_with_preset():
    from tv_app.application.services.tv_date_range_preset_service import (
        normalize_period_params_for_persistence,
    )

    out = normalize_period_params_for_persistence(
        {
            "dateRangePreset": "this_month",
            "start_date": _spec(MOTIVATING_START),
            "end_date": "2026-09-30",
        }
    )
    # Literal stale removida; ExpressionSpec deliberada preservada.
    assert "end_date" not in out
    assert out["start_date"] == _spec(MOTIVATING_START)
    assert out["dateRangePreset"] == "this_month"


def test_input_expression_overrides_source_preset_layer():
    """Input override com expressão vence preset do bloco."""
    merged = merge_data_params(
        playlist_defaults={},
        slide_filters={},
        block_params={"dateRangePreset": "this_year"},
        input_overrides={"start_date": _spec(MOTIVATING_START)},
    )
    out = resolve_param_expressions(
        merged, route=ROUTE, context=_ctx(date(2026, 10, 2))
    )
    assert out.params["start_date"] == "2026-09-28"
    # Fim não-expression → materializado do preset herdado (this_year→hoje).
    assert out.params["end_date"] == "2026-10-02"


# ---------------------------------------------------------------------- catálogo


def test_capability_exposes_weekday_refs_and_new_functions():
    cap = expression_capability(transport="mcp")
    assert "weekday.<Monday..Sunday>" in cap["referenceKinds"]
    assert "weekday.<Monday..Sunday>" in cap["ast"]["refs"]
    names = {f["name"] for f in cap["functions"]}
    for required in (
        "Date.StartOfWeek",
        "Value.Coalesce",
        "Logic.Switch",
        "Number.Clamp",
        "List.Contains",
    ):
        assert required in names
    by_name = {f["name"]: f for f in cap["functions"]}
    assert by_name["Date.StartOfWeek"]["argumentTypes"] == [
        "date|datetime",
        "weekday",
    ]
    assert by_name["Date.StartOfWeek"]["returnType"] == "date"
    assert by_name["Value.Coalesce"]["lazyArgs"] == "all"
    # Exemplo canônico do caso motivador presente e válido.
    example = cap["ast"]["examples"]["weekStartOfCurrentMonth"]
    node = CompiledExpression.from_dict(example)
    assert node.value == "Date.StartOfWeek"


def test_capability_actions_transport_is_compact():
    cap = expression_capability(transport="actions")
    assert cap["detailTransport"] == "mcp"
    assert "functions" not in cap


# ------------------------------------------------------------------ segurança


def test_no_eval_like_escape():
    """AST fechado: kind/value fora do allowlist falham na compilação."""
    with pytest.raises(Exception):
        compile_expression_spec(
            _spec({"kind": "call", "value": "os.system", "children": []}),
            phase=ExpressionPhase.PARAMETER,
            allowed_identifiers=frozenset({"today"}),
        )
    with pytest.raises(Exception):
        CompiledExpression.from_dict({"kind": "eval", "value": "x"})


def test_expression_not_allowed_on_locked_or_path_param():
    out = resolve_param_expressions(
        {"locked": _spec(_lit("x")), "slug": _spec(_lit("y"))},
        route=ROUTE,
        context=_ctx(date(2026, 10, 2)),
    )
    assert out.error is not None
    assert out.error["code"] == "m.expression_param_not_allowed"
