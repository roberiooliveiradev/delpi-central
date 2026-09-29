"""Expressões tipadas persistidas em ``dataBinding.params`` (fase PARAMETER).

Valor de parâmetro como dado, não código:

    params["start_date"] = {
        "expression": {"version": 1, "expression": <CompiledExpression JSON>}
    }

A especificação desserializa para ``CompiledExpression`` (IR do subsistema M)
e é avaliada por ``evaluate_compiled_expression`` — não existe segundo motor.
A resolução acontece depois de ``merge_data_params`` e antes da validação de
rota/AuthZ; o resultado é sempre um escalar compatível com o ``paramSchema``
da rota, que permanece o contrato final no wire.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Mapping
from zoneinfo import ZoneInfo

from tv_app.application.services.data.m_query.m_expression_interpreter import (
    MExpressionError,
    convert_m_value,
    evaluate_compiled_expression,
)
from tv_app.application.services.data.m_query.m_function_registry import (
    get_function_registry,
)
from tv_app.application.services.tv_dashboard_content_service import (
    m_query_setting,
    value_expression_setting,
)
from tv_app.application.services.tv_date_range_preset_service import (
    DEFAULT_BUSINESS_TIMEZONE,
    business_timezone_name,
    calendar_today,
)
from tv_app.domain.data_query.transform_plan import (
    CompiledExpression,
    ExpressionSpecError,
    expression_ast_node_contract,
)

EXPRESSION_PARAM_MARKER = "expression"
EXPRESSION_SPEC_VERSION = 1

# Referências de contexto canônicas injetadas via EvaluationContext.
CONTEXT_TODAY = "today"
CONTEXT_NOW = "now"
PARAM_REF_PREFIX = "param."


class ExpressionPhase(StrEnum):
    PARAMETER = "parameter"
    DERIVED_VALUE = "derivedValue"


_PARAMETER_KINDS = frozenset({"literal", "identifier", "call", "binary", "unary", "if", "list"})
_DERIVED_EXTRA_KINDS = frozenset({"field", "record", "recordField", "each", "type"})

_SCALAR_VALUE_TYPES = (str, int, float, bool)


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    """Contexto determinístico de avaliação — nunca lê o relógio no AST."""

    today: date
    now: datetime
    timezone: str
    culture: str


@dataclass(frozen=True, slots=True)
class ParamExpressionResolution:
    params: dict[str, Any]
    trace: list[dict[str, Any]]
    error: dict[str, Any] | None


def build_evaluation_context(
    *,
    today: date | None = None,
    now: datetime | None = None,
    culture: str | None = None,
) -> EvaluationContext:
    tz_name = business_timezone_name()
    resolved_today = calendar_today(today=today, tz_name=tz_name)
    if now is not None:
        resolved_now = now
    else:
        try:
            resolved_now = datetime.now(ZoneInfo(tz_name)).replace(tzinfo=None)
        except Exception:
            resolved_now = datetime.now()
    return EvaluationContext(
        today=resolved_today,
        now=resolved_now,
        timezone=tz_name or DEFAULT_BUSINESS_TIMEZONE,
        culture=str(culture or m_query_setting("defaultCulture", "pt-BR")),
    )


def is_expression_value(value: Any) -> bool:
    """True quando o valor persistido é um ExpressionSpec (dict marcador)."""
    return isinstance(value, Mapping) and isinstance(
        value.get(EXPRESSION_PARAM_MARKER), Mapping
    )


def params_contain_expressions(*layers: Any) -> bool:
    for layer in layers:
        if not isinstance(layer, Mapping):
            continue
        if any(is_expression_value(value) for value in layer.values()):
            return True
    return False


def _fail(code: str, message: str) -> None:
    raise MExpressionError(code, message)


def param_spec_expected_mtype(spec: Mapping[str, Any] | None) -> str | None:
    """Ponte paramSchema → MType (única fonte de mapeamento de tipos)."""
    if not isinstance(spec, Mapping):
        return None
    field_type = str(spec.get("type") or "").strip().lower()
    fmt = str(spec.get("format") or "").strip().lower()
    if fmt == "datetime" or field_type == "datetime":
        return "datetime"
    if fmt == "date" or field_type == "date":
        return "date"
    if field_type in {"integer", "number"}:
        return "number"
    if field_type == "boolean":
        return "logical"
    if field_type == "string" or isinstance(spec.get("enum"), list):
        return "text"
    return None


def param_allows_expression(param_name: str, route: Mapping[str, Any] | None) -> bool:
    """Expressão só vale em param declarado no paramSchema da rota (query)."""
    if not isinstance(route, Mapping):
        return False
    schema = route.get("paramSchema")
    if not isinstance(schema, Mapping):
        return False
    spec = schema.get(param_name)
    if not isinstance(spec, Mapping):
        return False
    if str(spec.get("in") or "").strip().lower() == "path":
        return False
    if spec.get("expressionAllowed") is False:
        return False
    fixed = route.get("fixedQueryParams")
    if isinstance(fixed, Mapping) and param_name in fixed:
        return False
    return True


def _check_identifier(name: str, allowed: frozenset[str]) -> None:
    if name in allowed:
        return
    _fail(
        "m.expression_reference_not_allowed",
        f'Referência "{name}" não disponível nesta fase da expressão.',
    )


def _walk_phase(
    node: CompiledExpression,
    phase: ExpressionPhase,
    allowed_identifiers: frozenset[str],
) -> None:
    allowed_kinds = _PARAMETER_KINDS | (
        _DERIVED_EXTRA_KINDS if phase == ExpressionPhase.DERIVED_VALUE else frozenset()
    )
    registry = get_function_registry()

    def visit(item: CompiledExpression) -> None:
        if item.kind not in allowed_kinds:
            _fail(
                "m.expression_reference_not_allowed",
                f"Nó {item.kind} não é permitido na fase {phase}.",
            )
        if item.kind == "identifier":
            _check_identifier(str(item.value or ""), allowed_identifiers)
        if item.kind == "call":
            name = str(item.value or "")
            spec = registry.resolve(name)
            if spec is None or spec.kind != "scalar":
                _fail(
                    "m.expression_operator_not_allowed",
                    f"A função {name} não é permitida em expressão de parâmetro.",
                )
            arity = len(item.children)
            if arity < spec.min_args or arity > spec.max_args:
                _fail(
                    "m.expression_schema_invalid",
                    f"A função {name} exige {spec.min_args}–{spec.max_args} argumento(s).",
                )
        for child in item.children:
            visit(child)

    visit(node)


def compile_expression_spec(
    raw_value: Any,
    *,
    phase: ExpressionPhase,
    allowed_identifiers: frozenset[str],
) -> CompiledExpression:
    """ExpressionSpec persistido → CompiledExpression validado (sem fallback)."""
    if not is_expression_value(raw_value):
        _fail(
            "m.expression_schema_invalid",
            "Valor de parâmetro não é um ExpressionSpec válido.",
        )
    spec = raw_value.get(EXPRESSION_PARAM_MARKER)
    assert isinstance(spec, Mapping)
    if spec.get("version") != EXPRESSION_SPEC_VERSION:
        _fail(
            "m.expression_schema_invalid",
            "Versão de ExpressionSpec não suportada.",
        )
    payload = spec.get("expression")
    try:
        node = CompiledExpression.from_dict(
            payload,
            max_depth=int(value_expression_setting("maxDepth", 40)),
            max_nodes=int(value_expression_setting("maxNodes", 256)),
            max_string_bytes=int(value_expression_setting("maxStringBytes", 512)),
        )
    except ExpressionSpecError as exc:
        raise MExpressionError(exc.code, str(exc)) from exc
    _walk_phase(node, phase, allowed_identifiers)
    return node


def _environment(
    context: EvaluationContext,
    merged_params: Mapping[str, Any],
) -> dict[str, Any]:
    env: dict[str, Any] = {
        CONTEXT_TODAY: context.today,
        CONTEXT_NOW: context.now,
    }
    for key, value in merged_params.items():
        if is_expression_value(value):
            continue
        if isinstance(value, _SCALAR_VALUE_TYPES):
            env[f"{PARAM_REF_PREFIX}{key}"] = value
    return env


def _allowed_param_identifiers(schema: Mapping[str, Any]) -> frozenset[str]:
    names = {CONTEXT_TODAY, CONTEXT_NOW}
    for key in schema.keys():
        names.add(f"{PARAM_REF_PREFIX}{key}")
    return frozenset(names)


def _coerce_result(
    value: Any,
    *,
    param_name: str,
    spec: Mapping[str, Any] | None,
    culture: str,
) -> Any:
    if value is None:
        _fail(
            "m.expression_null_result",
            f"A expressão do parâmetro {param_name} produziu null.",
        )
    expected = param_spec_expected_mtype(spec)
    if expected == "date":
        resolved = convert_m_value(value, "date", culture)
        return resolved.isoformat()
    if expected == "datetime":
        resolved = convert_m_value(value, "datetime", culture)
        return resolved.isoformat()
    if expected == "number":
        number = convert_m_value(value, "number", culture)
        if str((spec or {}).get("type") or "").lower() == "integer":
            if not float(number).is_integer():
                _fail(
                    "m.expression_type_mismatch",
                    f"A expressão do parâmetro {param_name} não produziu inteiro.",
                )
            return int(number)
        return int(number) if float(number).is_integer() else float(number)
    if expected == "logical":
        return convert_m_value(value, "logical", culture)
    if expected == "text" or expected is None:
        if expected is None and not isinstance(
            value, (*_SCALAR_VALUE_TYPES, date, datetime)
        ):
            _fail(
                "m.expression_type_mismatch",
                f"A expressão do parâmetro {param_name} não produziu valor escalar.",
            )
        text = convert_m_value(value, "text", culture)
        enum_values = (spec or {}).get("enum") if isinstance(spec, Mapping) else None
        if isinstance(enum_values, list) and enum_values:
            allowed = {str(item).strip() for item in enum_values}
            if str(text).strip() not in allowed:
                _fail(
                    "m.expression_type_mismatch",
                    f"A expressão do parâmetro {param_name} produziu valor fora do enum.",
                )
        if expected == "text":
            return text
        return value if isinstance(value, _SCALAR_VALUE_TYPES) else text
    _fail(
        "m.expression_type_mismatch",
        f"A expressão do parâmetro {param_name} produziu tipo incompatível.",
    )


def resolve_param_expressions(
    merged_params: Mapping[str, Any] | None,
    *,
    route: Mapping[str, Any] | None,
    context: EvaluationContext | None = None,
) -> ParamExpressionResolution:
    """Resolve ExpressionSpecs em params merged → escalares + trace tipado.

    Ordem canônica: merge_data_params → esta função → validação de rota/AuthZ
    → preset/defaults → wire. Em erro, ``error`` vem preenchido e o caller não
    deve chamar a rota (error != empty).
    """
    params = dict(merged_params) if isinstance(merged_params, Mapping) else {}
    trace: list[dict[str, Any]] = []
    expression_keys = [
        key for key, value in params.items() if is_expression_value(value)
    ]
    if not expression_keys:
        return ParamExpressionResolution(params=params, trace=trace, error=None)
    if not bool(value_expression_setting("enabled", True)):
        return ParamExpressionResolution(
            params=params,
            trace=trace,
            error={
                "code": "m.expression_disabled",
                "message": "Expressões de parâmetro estão desabilitadas.",
            },
        )
    ctx = context or build_evaluation_context()
    schema = (
        route.get("paramSchema")
        if isinstance(route, Mapping) and isinstance(route.get("paramSchema"), Mapping)
        else {}
    )
    allowed_ids = _allowed_param_identifiers(schema)
    env = _environment(ctx, params)
    for key in expression_keys:
        raw = params[key]
        entry: dict[str, Any] = {
            "param": str(key),
            "expression": raw.get(EXPRESSION_PARAM_MARKER),
            "expectedType": param_spec_expected_mtype(schema.get(key))
            if isinstance(schema.get(key), Mapping)
            else None,
        }
        try:
            if not param_allows_expression(str(key), route):
                _fail(
                    "m.expression_param_not_allowed",
                    f"O parâmetro {key} não aceita expressão nesta rota.",
                )
            node = compile_expression_spec(
                raw,
                phase=ExpressionPhase.PARAMETER,
                allowed_identifiers=allowed_ids,
            )
            value = evaluate_compiled_expression(
                node,
                environment=env,
                culture=ctx.culture,
                max_depth=int(value_expression_setting("maxDepth", 40)),
            )
            wire = _coerce_result(
                value,
                param_name=str(key),
                spec=schema.get(key) if isinstance(schema.get(key), Mapping) else None,
                culture=ctx.culture,
            )
        except MExpressionError as exc:
            entry["error"] = {"code": exc.code, "message": str(exc)}
            trace.append(entry)
            return ParamExpressionResolution(
                params=params,
                trace=trace,
                error=entry["error"] | {"param": str(key)},
            )
        params[str(key)] = wire
        entry["resolved"] = wire
        trace.append(entry)
    return ParamExpressionResolution(params=params, trace=trace, error=None)


def validate_expression_param_value(
    param_name: str,
    raw_value: Any,
    *,
    route: Mapping[str, Any] | None,
) -> None:
    """Validação de escrita: spec + fase + refs (o tipo de saída só é avaliado
    no runtime — a coerção fica em ``_coerce_result``)."""
    schema = (
        route.get("paramSchema")
        if isinstance(route, Mapping) and isinstance(route.get("paramSchema"), Mapping)
        else {}
    )
    if not param_allows_expression(param_name, route):
        _fail(
            "m.expression_param_not_allowed",
            f"O parâmetro {param_name} não aceita expressão nesta rota.",
        )
    compile_expression_spec(
        raw_value,
        phase=ExpressionPhase.PARAMETER,
        allowed_identifiers=_allowed_param_identifiers(schema),
    )


def assert_no_unresolved_expressions(params: Mapping[str, Any] | None) -> None:
    """Defense-in-depth: o wire nunca recebe ExpressionSpec não avaliado."""
    if not isinstance(params, Mapping):
        return
    offending = sorted(
        str(key) for key, value in params.items() if is_expression_value(value)
    )
    if offending:
        _fail(
            "m.expression_unresolved",
            "Parâmetro com expressão chegou ao gateway sem avaliação: "
            + ", ".join(offending),
        )


# Exemplos canônicos de AST — cada um deve passar por CompiledExpression.from_dict
# + validação de fase PARAMETER (garantido por teste de drift no catálogo).
_CATALOG_AST_EXAMPLES: dict[str, dict[str, Any]] = {
    "today": {"kind": "identifier", "value": CONTEXT_TODAY},
    "previousYearSameDay": {
        "kind": "call",
        "value": "Date.AddMonths",
        "children": [
            {"kind": "identifier", "value": CONTEXT_TODAY},
            {"kind": "literal", "value": -12},
        ],
    },
    "previousYearMonthStart": {
        "kind": "call",
        "value": "Date.StartOfMonth",
        "children": [
            {
                "kind": "call",
                "value": "Date.AddMonths",
                "children": [
                    {"kind": "identifier", "value": CONTEXT_TODAY},
                    {"kind": "literal", "value": -12},
                ],
            }
        ],
    },
    "yearStart": {
        "kind": "call",
        "value": "Date.StartOfYear",
        "children": [{"kind": "identifier", "value": CONTEXT_TODAY}],
    },
    "numericVariationPct": {
        "kind": "binary",
        "value": "*",
        "children": [
            {
                "kind": "binary",
                "value": "-",
                "children": [
                    {
                        "kind": "binary",
                        "value": "/",
                        "children": [
                            {"kind": "literal", "value": 120},
                            {"kind": "literal", "value": 100},
                        ],
                    },
                    {"kind": "literal", "value": 1},
                ],
            },
            {"kind": "literal", "value": 100},
        ],
    },
}


def _parameter_ast_contract() -> dict[str, Any]:
    """Projeção de authoring PARAMETER filtrada do contrato canônico do loader."""
    contract = expression_ast_node_contract()
    return {
        "nodeKeys": contract["nodeKeys"],
        "nodeKinds": {
            kind: contract["nodeKinds"][kind]
            for kind in sorted(_PARAMETER_KINDS)
        },
        "operators": contract["operators"],
        "literalTypes": contract["literalTypes"],
        # Mapeamento ref → JSON exato: VISTA/UI nunca inventam shape.
        "refs": {
            f"context:{CONTEXT_TODAY}": {
                "kind": "identifier",
                "value": CONTEXT_TODAY,
            },
            f"context:{CONTEXT_NOW}": {
                "kind": "identifier",
                "value": CONTEXT_NOW,
            },
            "param.<schemaParam>": {
                "kind": "identifier",
                "value": "param.<schemaParam>",
            },
        },
        "literalValue": "kind=literal; value = escalar JSON (str|number|bool|null) — tipo inferido do JSON",
        "callShape": 'kind=call; value=<functionName>; children=[args...] na ordem dos parâmetros da signature',
        "examples": _CATALOG_AST_EXAMPLES,
    }


def expression_capability(*, transport: str = "mcp") -> dict[str, Any]:
    """Bloco de capability de expressões para a projeção de catálogo (VISTA).

    ``transport="actions"`` projeta apenas um stub: o envelope de Actions tem
    teto ~100 KiB (OpenAI) sem folga residual — o contrato completo de
    expressões é MCP-primary e também visível em ``/data/m/functions``.
    """
    if transport == "actions":
        return {
            "version": EXPRESSION_SPEC_VERSION,
            "enabled": bool(value_expression_setting("enabled", True)),
            "detailTransport": "mcp",
        }
    registry = get_function_registry()
    return {
        "version": EXPRESSION_SPEC_VERSION,
        "enabled": bool(value_expression_setting("enabled", True)),
        "phases": [ExpressionPhase.PARAMETER.value],
        "wireShape": 'params[name]={"expression":{"version":1,"expression":<ast>}}',
        "referenceKinds": [
            "literal",
            f"context:{CONTEXT_TODAY}",
            f"context:{CONTEXT_NOW}",
            "param.<schemaParam>",
        ],
        "functions": [
            spec.to_dict()
            for spec in registry.functions.values()
            if spec.kind == "scalar"
        ],
        "limits": {
            "maxDepth": int(value_expression_setting("maxDepth", 40)),
            "maxNodes": int(value_expression_setting("maxNodes", 256)),
            "maxStringBytes": int(value_expression_setting("maxStringBytes", 512)),
        },
        "paramPolicy": "paramSchema query params; spec.expressionAllowed=false opts out; path/fixed params denied",
        "writableVia": [
            "patch_data_source_params.set.<param>",
            "upsert_data_source.params.<param>",
            "upsert_data_model.model.inputs[].params.<param>",
        ],
        "ast": _parameter_ast_contract(),
    }
