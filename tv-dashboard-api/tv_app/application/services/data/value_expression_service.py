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
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from tv_app.application.services.data.m_query.m_expression_interpreter import (
    MExpressionError,
    WEEKDAY_CONSTANTS,
    convert_m_value,
    evaluate_compiled_expression,
)
from tv_app.application.services.data.m_query.m_expression_typecheck import (
    TYPE_ANY,
    TYPE_DATE,
    TYPE_DATETIME,
    TYPE_WEEKDAY,
    check_output_type,
    typecheck_expression,
)
from tv_app.application.services.data.m_query.m_function_registry import (
    get_function_registry,
)
from tv_app.application.services.tv_dashboard_content_service import (
    m_query_setting,
    value_expression_setting,
)
from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    DEFAULT_BUSINESS_TIMEZONE,
    DEFAULT_DATE_RANGE_KEYS,
    END_KEYS,
    PERIOD_DAYS_KEY,
    START_KEYS,
    business_timezone_name,
    calendar_today,
    compute_preset_range,
    find_date_range_keys,
    resolve_output_date_range_keys,
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
# Variáveis de input do slide — namespace separado de ``param.*``; nunca vão ao wire.
INPUT_REF_PREFIX = "input."
INPUT_VARIABLE_KEY_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")


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
class InputVariableScope:
    """Variáveis ``input.<key>`` declaradas no slide, já validadas pelo contrato.

    ``schemas``: key → valueSchema; ``values``: key → valor tipado efetivo
    (override de sessão válido → defaultValue; ausente = sem valor);
    ``invalid``: key → código do override rejeitado (fail closed em quem referencia).
    """

    schemas: Mapping[str, Mapping[str, Any]] = field(default_factory=dict)
    values: Mapping[str, Any] = field(default_factory=dict)
    invalid: Mapping[str, str] = field(default_factory=dict)


EMPTY_INPUT_SCOPE = InputVariableScope()


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
            if spec is None or spec.kind != "scalar" or (
                phase == ExpressionPhase.PARAMETER and not spec.parameter_expression
            ):
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
    identifier_types: Mapping[str, str] | None = None,
    expected_type: str | None = None,
    param_name: str | None = None,
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
    if phase == ExpressionPhase.PARAMETER and identifier_types is not None:
        # Gate estático pré-avaliação: falha antes do fetch e do persist.
        root_path = str(param_name or "")
        actual = typecheck_expression(
            node,
            registry=get_function_registry(),
            identifier_types=identifier_types,
            path=root_path,
        )
        check_output_type(
            actual,
            expected=expected_type,
            param_name=root_path,
            path=root_path,
        )
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
    names = {CONTEXT_TODAY, CONTEXT_NOW, *WEEKDAY_CONSTANTS}
    for key in schema.keys():
        names.add(f"{PARAM_REF_PREFIX}{key}")
    return frozenset(names)


def _identifier_types(schema: Mapping[str, Any]) -> dict[str, str]:
    # Refs tipadas do contexto PARAMETER — única fonte para o typecheck.
    types: dict[str, str] = {
        CONTEXT_TODAY: TYPE_DATE,
        CONTEXT_NOW: TYPE_DATETIME,
        **{name: TYPE_WEEKDAY for name in WEEKDAY_CONSTANTS},
    }
    for key, spec in schema.items():
        expected = (
            param_spec_expected_mtype(spec) if isinstance(spec, Mapping) else None
        )
        types[f"{PARAM_REF_PREFIX}{key}"] = expected or TYPE_ANY
    return types


def _parameter_reference_scope(
    schema: Mapping[str, Any],
    input_scope: InputVariableScope | None,
    *,
    deferred_input_keys: frozenset[str] = frozenset(),
) -> tuple[frozenset[str], dict[str, str]]:
    """Refs permitidas + tipos: contexto, ``param.<schema>`` e ``input.<declarada>``.

    ``deferred_input_keys``: refs ``input.*`` ainda não declaradas no estado
    parcial de uma op — tipo ANY; a declaração é exigida no nativeConfig candidato.
    """
    allowed = set(_allowed_param_identifiers(schema))
    types = _identifier_types(schema)
    scope = input_scope or EMPTY_INPUT_SCOPE
    for key, value_schema in scope.schemas.items():
        ref = f"{INPUT_REF_PREFIX}{key}"
        allowed.add(ref)
        types[ref] = param_spec_expected_mtype(value_schema) or TYPE_ANY
    for key in deferred_input_keys:
        ref = f"{INPUT_REF_PREFIX}{key}"
        if ref not in allowed:
            allowed.add(ref)
            types[ref] = TYPE_ANY
    return frozenset(allowed), types


def _input_environment(input_scope: InputVariableScope | None) -> dict[str, Any]:
    env: dict[str, Any] = {}
    scope = input_scope or EMPTY_INPUT_SCOPE
    for key, value in scope.values.items():
        if param_spec_expected_mtype(scope.schemas.get(key)) == "date" and isinstance(value, str):
            try:
                value = date.fromisoformat(value)
            except ValueError:
                continue
        env[f"{INPUT_REF_PREFIX}{key}"] = value
    return env


def _referenced_identifiers(node: CompiledExpression) -> set[str]:
    found: set[str] = set()
    stack = [node]
    while stack:
        item = stack.pop()
        if item.kind == "identifier":
            found.add(str(item.value or ""))
        stack.extend(item.children)
    return found


def expression_input_refs(raw_value: Any) -> frozenset[str]:
    """Keys ``input.<key>`` referenciadas por um ExpressionSpec (vazio se malformado)."""
    if not is_expression_value(raw_value):
        return frozenset()
    spec = raw_value.get(EXPRESSION_PARAM_MARKER)
    try:
        node = CompiledExpression.from_dict(
            spec.get("expression") if isinstance(spec, Mapping) else None,
            max_depth=int(value_expression_setting("maxDepth", 40)),
            max_nodes=int(value_expression_setting("maxNodes", 256)),
            max_string_bytes=int(value_expression_setting("maxStringBytes", 512)),
        )
    except ExpressionSpecError:
        return frozenset()
    return frozenset(
        name[len(INPUT_REF_PREFIX) :]
        for name in _referenced_identifiers(node)
        if name.startswith(INPUT_REF_PREFIX)
    )


def _assert_input_refs_bound(
    node: CompiledExpression, input_scope: InputVariableScope | None
) -> None:
    """Variável referenciada precisa ter valor válido — sem fallback silencioso."""
    scope = input_scope or EMPTY_INPUT_SCOPE
    for name in sorted(_referenced_identifiers(node)):
        if not name.startswith(INPUT_REF_PREFIX):
            continue
        key = name[len(INPUT_REF_PREFIX) :]
        if key in scope.invalid:
            _fail(
                "m.input_value_invalid",
                f'O valor selecionado para a variável "{key}" é inválido.',
            )
        if key not in scope.values:
            _fail(
                "m.input_value_missing",
                f'A variável "{key}" não tem valor (sem padrão nem seleção).',
            )


def _consume_preset_for_expression_overrides(
    params: dict[str, Any],
    *,
    route: Mapping[str, Any] | None,
    schema: Mapping[str, Any],
    resolved_keys: frozenset[str],
    today: date,
) -> tuple[str, str] | None:
    """Preset relativo é *default por ponta* frente a ExpressionSpec.

    Quando ao menos uma ponta do range foi resolvida por expressão, o preset
    materializa somente a ponta não-expression e é consumido aqui — o wire
    recebe somente datas concretas. Sem datas-expression → no-op e a
    materialização segue no gateway (``apply_date_range_preset``), que mantém
    a defesa anti-stale sobre literais.
    """
    preset = str(params.get(DATE_RANGE_PRESET_KEY) or "").strip()
    if not preset:
        return None
    start_resolved = bool(resolved_keys.intersection(START_KEYS))
    end_resolved = bool(resolved_keys.intersection(END_KEYS))
    if not (start_resolved or end_resolved):
        return None
    route_map = route if isinstance(route, Mapping) else {}
    pair = resolve_output_date_range_keys(
        schema_keys=schema,
        date_range_keys=route_map.get("dateRangeKeys"),
        strategy=str(route_map.get("paramStrategy") or "direct"),
    )
    if pair is None:
        pair = find_date_range_keys(params) or DEFAULT_DATE_RANGE_KEYS
    period_raw = params.get(PERIOD_DAYS_KEY)
    try:
        period_days = (
            int(period_raw) if period_raw is not None and period_raw != "" else None
        )
    except (TypeError, ValueError):
        period_days = None
    computed = compute_preset_range(preset, period_days=period_days, today=today)
    if computed is None:
        return None
    start_key, end_key = pair
    if not start_resolved:
        params[start_key] = computed[0].isoformat()
    if not end_resolved:
        params[end_key] = computed[1].isoformat()
    params.pop(DATE_RANGE_PRESET_KEY, None)
    return start_key, end_key


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
    input_scope: InputVariableScope | None = None,
) -> ParamExpressionResolution:
    """Resolve ExpressionSpecs em params merged → escalares + trace tipado.

    Ordem canônica: merge_data_params → esta função → validação de rota/AuthZ
    → preset/defaults → wire. Em erro, ``error`` vem preenchido e o caller não
    deve chamar a rota (error != empty). ``input_scope`` expõe ``input.<key>``
    só ao ambiente de avaliação — nunca entra em ``params``.
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
    allowed_ids, id_types = _parameter_reference_scope(schema, input_scope)
    registry = get_function_registry()
    env = _environment(ctx, params) | _input_environment(input_scope)
    for key in expression_keys:
        raw = params[key]
        entry: dict[str, Any] = {
            "param": str(key),
            "expression": raw.get(EXPRESSION_PARAM_MARKER),
            "expectedType": param_spec_expected_mtype(schema.get(key))
            if isinstance(schema.get(key), Mapping)
            else None,
            "timezone": ctx.timezone,
            "registryVersion": registry.version,
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
                identifier_types=id_types,
                expected_type=entry["expectedType"],
                param_name=str(key),
            )
            _assert_input_refs_bound(node, input_scope)
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
    resolved_keys = frozenset(
        str(item["param"]) for item in trace if "resolved" in item
    )
    consumed = _consume_preset_for_expression_overrides(
        params,
        route=route,
        schema=schema,
        resolved_keys=resolved_keys,
        today=ctx.today,
    )
    if consumed is not None:
        trace.append(
            {
                "param": DATE_RANGE_PRESET_KEY,
                "materializedAsDefaults": True,
                "filled": [
                    key for key in consumed if key not in resolved_keys
                ],
                "timezone": ctx.timezone,
            }
        )
    return ParamExpressionResolution(params=params, trace=trace, error=None)


def validate_expression_param_value(
    param_name: str,
    raw_value: Any,
    *,
    route: Mapping[str, Any] | None,
    input_scope: InputVariableScope | None = None,
    defer_undeclared_inputs: bool = False,
) -> None:
    """Validação de escrita: spec + fase + refs (o tipo de saída só é avaliado
    no runtime — a coerção fica em ``_coerce_result``).

    ``defer_undeclared_inputs``: validação por op (estado parcial) aceita
    ``input.<key>`` sintaticamente válido ainda não declarado; o nativeConfig
    candidato (``TvDataConfigValidationService``) exige a declaração.
    """
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
    deferred: frozenset[str] = frozenset()
    if defer_undeclared_inputs:
        declared = set((input_scope or EMPTY_INPUT_SCOPE).schemas)
        deferred = frozenset(
            key
            for key in expression_input_refs(raw_value)
            if key not in declared and INPUT_VARIABLE_KEY_PATTERN.match(key)
        )
    allowed_ids, id_types = _parameter_reference_scope(
        schema, input_scope, deferred_input_keys=deferred
    )
    compile_expression_spec(
        raw_value,
        phase=ExpressionPhase.PARAMETER,
        allowed_identifiers=allowed_ids,
        # Ref adiada ainda não tem tipo: o typecheck completo roda no candidato.
        identifier_types=None if deferred else id_types,
        expected_type=param_spec_expected_mtype(schema.get(param_name)),
        param_name=param_name,
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


def scope_layer_expressions_to_route(
    params: Mapping[str, Any] | None,
    *,
    route: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Scoping de ExpressionSpec em camada compartilhada (tela/programação).

    A expressão da camada aplica-se apenas às rotas que declaram e permitem
    o parâmetro — mesmo scoping que o wire dá a literais fora do schema
    (``_filter_query_to_route_schema``). Params da fonte/input NÃO passam
    por aqui: na camada da fonte, expressão em chave não permitida segue
    sendo erro no resolver.
    """
    if not isinstance(params, Mapping):
        return {}
    out: dict[str, Any] = {}
    for key, value in params.items():
        if is_expression_value(value) and not param_allows_expression(
            str(key), route
        ):
            continue
        out[str(key)] = value
    return out


def validate_shared_layer_expressions(
    params: Mapping[str, Any] | None,
    *,
    routes: Sequence[Mapping[str, Any]],
    input_scope: InputVariableScope | None = None,
) -> None:
    """Validação de escrita para ExpressionSpec em ``dataFilters``/``dataDefaults``.

    ``input_scope``: variáveis do slide (só ``dataFilters``); ``dataDefaults`` da
    programação não tem slide, então ``input.*`` segue proibido ali.

    Regra do escopo: a chave precisa ser declarada no ``paramSchema`` de ≥1
    rota consumidora e nenhuma rota que a declara pode proibir expressão
    nela (``expressionAllowed: false`` / ``in: path``). ``fixedQueryParams``
    apenas excluem a rota do escopo (runtime faz o scoping), não vetam.
    AST/refs/tipos compilam contra o union schema do escopo.
    """
    if not isinstance(params, Mapping):
        return
    route_list = [r for r in routes if isinstance(r, Mapping)]
    union_schema: dict[str, Any] = {}
    for route in route_list:
        schema = route.get("paramSchema")
        if isinstance(schema, Mapping):
            for key, spec in schema.items():
                union_schema.setdefault(str(key), spec)
    union_route: dict[str, Any] = {"paramSchema": union_schema}
    for key, value in params.items():
        if not is_expression_value(value):
            continue
        key_s = str(key)
        declaring = [
            r
            for r in route_list
            if isinstance(r.get("paramSchema"), Mapping)
            and key_s in r["paramSchema"]
        ]
        if not declaring:
            _fail(
                "m.expression_param_not_allowed",
                f"O parâmetro {key_s} não existe nas rotas deste escopo.",
            )
        forbidden = [
            r
            for r in declaring
            if str(
                (r["paramSchema"].get(key_s) or {}).get("in") or ""
            ).strip().lower()
            == "path"
            or (r["paramSchema"].get(key_s) or {}).get("expressionAllowed")
            is False
        ]
        if forbidden:
            _fail(
                "m.expression_param_not_allowed",
                f"O parâmetro {key_s} não aceita expressão em todas as rotas "
                "que o declaram neste escopo.",
            )
        validate_expression_param_value(
            key_s, value, route=union_route, input_scope=input_scope
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
    "weekStartOfCurrentMonth": {
        "kind": "call",
        "value": "Date.StartOfWeek",
        "children": [
            {
                "kind": "call",
                "value": "Date.StartOfMonth",
                "children": [{"kind": "identifier", "value": CONTEXT_TODAY}],
            },
            {"kind": "identifier", "value": "Monday"},
        ],
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
            "weekday.<Monday..Sunday>": {
                "kind": "identifier",
                "value": "Monday",
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
            "weekday.<Monday..Sunday>",
        ],
        "functions": [
            spec.to_dict()
            for spec in registry.functions.values()
            if spec.kind == "scalar" and spec.parameter_expression
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
            "patch_data_model.inputPatches[].params.set.<param>",
        ],
        "ast": _parameter_ast_contract(),
    }
