"""Type checking estático de CompiledExpression na fase PARAMETER.

Determinístico e pré-execução: usa os metadados declarativos do registry
(``argumentTypes``/``returnType``) — nunca infere tipo parseando assinatura.
Erros carregam diagnóstico estruturado (function/argument/expected/received/
expressionPath) para correção por VISTA/UI.
"""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.m_query.m_expression_interpreter import (
    MExpressionError,
)
from tv_app.application.services.data.m_query.m_function_registry import (
    MFunctionRegistry,
)
from tv_app.domain.data_query.transform_plan import CompiledExpression

# Tipos do sistema PARAMETER (espelham convert_m_value + weekday enum).
TYPE_TEXT = "text"
TYPE_NUMBER = "number"
TYPE_LOGICAL = "logical"
TYPE_DATE = "date"
TYPE_DATETIME = "datetime"
TYPE_DURATION = "duration"
TYPE_LIST = "list"
TYPE_WEEKDAY = "weekday"
TYPE_NULL = "null"
TYPE_ANY = "any"
TYPE_UNKNOWN = "unknown"

_COMPARABLE = frozenset({TYPE_NUMBER, TYPE_WEEKDAY, TYPE_DATE, TYPE_DATETIME, TYPE_TEXT})
_ORDERED = frozenset({TYPE_NUMBER, TYPE_WEEKDAY, TYPE_DATE, TYPE_DATETIME, TYPE_TEXT})


def _fail(code: str, message: str, **details: Any) -> None:
    path = details.pop("expressionPath", None)
    raise MExpressionError(
        code, message, details=details, expression_path=path
    )


def _split_union(type_name: str) -> frozenset[str]:
    return frozenset(part.strip() for part in str(type_name or "").split("|") if part.strip())


def _is_assignable(actual: str, expected: str) -> bool:
    """True quando o tipo inferido satisfaz o tipo declarado do registry."""
    if expected in {TYPE_ANY, ""} or actual == TYPE_UNKNOWN:
        return True
    options = _split_union(expected)
    if TYPE_ANY in options or actual in options:
        return True
    if actual == TYPE_NULL:
        return True  # null é atribuível — a coerção final decide
    if actual == TYPE_WEEKDAY and TYPE_NUMBER in options:
        return True
    if actual == TYPE_DATE and TYPE_DATETIME in options:
        return True
    if actual == TYPE_NUMBER and TYPE_WEEKDAY in options:
        return True
    return False


def _join(left: str, right: str) -> str:
    if left == right:
        return left
    if TYPE_ANY in {left, right} or TYPE_UNKNOWN in {left, right}:
        return TYPE_ANY
    if TYPE_NULL in {left, right}:
        return right if left == TYPE_NULL else left
    pair = {left, right}
    if pair == {TYPE_DATE, TYPE_DATETIME}:
        return TYPE_DATETIME
    if pair == {TYPE_NUMBER, TYPE_WEEKDAY}:
        return TYPE_NUMBER
    return TYPE_ANY


def _literal_type(value: Any) -> str:
    if value is None:
        return TYPE_NULL
    if isinstance(value, bool):
        return TYPE_LOGICAL
    if isinstance(value, (int, float)):
        return TYPE_NUMBER
    if isinstance(value, str):
        return TYPE_TEXT
    return TYPE_UNKNOWN


def typecheck_expression(
    node: CompiledExpression,
    *,
    registry: MFunctionRegistry,
    identifier_types: Mapping[str, str],
    path: str = "",
) -> str:
    """Infere o tipo do nó ou falha com diagnóstico estruturado.

    ``identifier_types`` mapeia refs tipadas do contexto
    (today→date, now→datetime, Monday..Sunday→weekday, param.<x>→tipo do schema).
    """
    kind = node.kind
    if kind == "literal":
        return _literal_type(node.value)
    if kind == "identifier":
        name = str(node.value or "")
        declared = identifier_types.get(name)
        if declared is None:
            _fail(
                "m.unknown_identifier",
                f'O identificador "{name}" não foi encontrado.',
                expected="|".join(sorted(identifier_types))[:200],
                received=name,
                expressionPath=path,
            )
        return declared
    if kind == "list":
        element_type = TYPE_ANY
        for index, child in enumerate(node.children):
            child_type = typecheck_expression(
                child,
                registry=registry,
                identifier_types=identifier_types,
                path=f"{path}.children[{index}]",
            )
            joined = _join(element_type, child_type)
            if joined == TYPE_ANY and element_type != child_type and TYPE_ANY not in {
                element_type,
                child_type,
            }:
                _fail(
                    "expression.type_mismatch",
                    "A lista mistura tipos incompatíveis.",
                    expected=element_type,
                    received=child_type,
                    expressionPath=f"{path}.children[{index}]",
                )
            element_type = joined
        return TYPE_LIST
    if kind == "unary":
        operand = typecheck_expression(
            node.children[0],
            registry=registry,
            identifier_types=identifier_types,
            path=f"{path}.children[0]",
        )
        operator = str(node.value)
        if operator == "not":
            if not _is_assignable(operand, TYPE_LOGICAL):
                _fail(
                    "expression.type_mismatch",
                    "O operador not exige logical.",
                    expected=TYPE_LOGICAL,
                    received=operand,
                    expressionPath=f"{path}.children[0]",
                )
            return TYPE_LOGICAL
        if not _is_assignable(operand, TYPE_NUMBER):
            _fail(
                "expression.type_mismatch",
                f"O operador {operator} exige number.",
                expected=TYPE_NUMBER,
                received=operand,
                expressionPath=f"{path}.children[0]",
            )
        return TYPE_NUMBER
    if kind == "binary":
        operator = str(node.value)
        left = typecheck_expression(
            node.children[0],
            registry=registry,
            identifier_types=identifier_types,
            path=f"{path}.children[0]",
        )
        right = typecheck_expression(
            node.children[1],
            registry=registry,
            identifier_types=identifier_types,
            path=f"{path}.children[1]",
        )
        if operator in {"and", "or"}:
            for side, value in (("0", left), ("1", right)):
                if not _is_assignable(value, TYPE_LOGICAL):
                    _fail(
                        "expression.type_mismatch",
                        f"O operador {operator} exige operandos logical.",
                        expected=TYPE_LOGICAL,
                        received=value,
                        argument=int(side),
                        expressionPath=f"{path}.children[{side}]",
                    )
            return TYPE_LOGICAL
        if operator in {"=", "<>"}:
            pair = {left, right}
            comparable = (
                left == right
                or TYPE_ANY in pair
                or TYPE_NULL in pair
                or pair <= {TYPE_NUMBER, TYPE_WEEKDAY}
                or pair <= {TYPE_DATE, TYPE_DATETIME}
            )
            if not comparable:
                _fail(
                    "expression.type_mismatch",
                    f"O operador {operator} exige tipos compatíveis.",
                    expected=left,
                    received=right,
                    argument=1,
                    expressionPath=f"{path}.children[1]",
                )
            return TYPE_LOGICAL
        if operator in {">", ">=", "<", "<="}:
            joined = _join(left, right)
            for side, value in (("0", left), ("1", right)):
                if (
                    value not in {TYPE_ANY, TYPE_UNKNOWN, TYPE_NULL}
                    and value not in _ORDERED
                ):
                    _fail(
                        "expression.type_mismatch",
                        f"O operador {operator} exige tipos ordenáveis.",
                        expected="number|date|datetime|text|weekday",
                        received=value,
                        argument=int(side),
                        expressionPath=f"{path}.children[{side}]",
                    )
            if joined == TYPE_ANY and left != right:
                _fail(
                    "expression.type_mismatch",
                    f"O operador {operator} exige operandos do mesmo domínio.",
                    expected=left,
                    received=right,
                    argument=1,
                    expressionPath=f"{path}.children[1]",
                )
            return TYPE_LOGICAL
        if operator == "&":
            return TYPE_TEXT
        # aritmética
        for side, value in (("0", left), ("1", right)):
            if not _is_assignable(value, TYPE_NUMBER):
                _fail(
                    "expression.type_mismatch",
                    f"O operador {operator} exige operandos number.",
                    expected=TYPE_NUMBER,
                    received=value,
                    argument=int(side),
                    expressionPath=f"{path}.children[{side}]",
                )
        return TYPE_NUMBER
    if kind == "if":
        condition = typecheck_expression(
            node.children[0],
            registry=registry,
            identifier_types=identifier_types,
            path=f"{path}.children[0]",
        )
        if not _is_assignable(condition, TYPE_LOGICAL):
            _fail(
                "expression.type_mismatch",
                "A condição do if exige logical.",
                expected=TYPE_LOGICAL,
                received=condition,
                expressionPath=f"{path}.children[0]",
            )
        then_type = typecheck_expression(
            node.children[1],
            registry=registry,
            identifier_types=identifier_types,
            path=f"{path}.children[1]",
        )
        else_type = typecheck_expression(
            node.children[2],
            registry=registry,
            identifier_types=identifier_types,
            path=f"{path}.children[2]",
        )
        return _join(then_type, else_type)
    if kind == "call":
        name = str(node.value or "")
        spec = registry.resolve(name)
        if spec is None:
            _fail(
                "m.function_not_allowed",
                f"A função {name} não existe no registry.",
                function=name,
                expressionPath=path,
            )
        assert spec is not None
        arity = len(node.children)
        if arity < spec.min_args or arity > spec.max_args:
            _fail(
                "expression.arity_mismatch",
                f"A função {name} exige {spec.min_args}–{spec.max_args} argumento(s).",
                function=name,
                expected=f"{spec.min_args}..{spec.max_args}",
                received=str(arity),
                expressionPath=path,
            )
        for index, child in enumerate(node.children):
            child_type = typecheck_expression(
                child,
                registry=registry,
                identifier_types=identifier_types,
                path=f"{path}.children[{index}]",
            )
            if not spec.argument_types:
                continue
            declared = spec.argument_types[
                min(index, len(spec.argument_types) - 1)
            ]
            if not _is_assignable(child_type, declared):
                _fail(
                    "expression.type_mismatch",
                    f"Argumento {index} de {name} incompatível.",
                    function=name,
                    argument=index,
                    expected=declared,
                    received=child_type,
                    expressionPath=f"{path}.children[{index}]",
                )
        return spec.return_type
    _fail(
        "m.expression_not_supported",
        f"Nó {kind} não é suportado na fase de parâmetros.",
        expressionPath=path,
    )
    return TYPE_UNKNOWN


def check_output_type(
    actual: str,
    *,
    expected: str | None,
    param_name: str,
    path: str = "",
) -> None:
    """Saída final vs tipo esperado do paramSchema da rota.

    Espelha _coerce_result: text aceita qualquer escalar (a coerção de
    runtime é total); demais tipos exigem atribuível — divergência falha antes
    do fetch e antes de persistir.
    """
    if not expected or expected == TYPE_ANY:
        return
    if expected == TYPE_DATE and actual == TYPE_DATETIME:
        return  # truncamento determinístico — mesma coerção de _coerce_result
    if expected == TYPE_TEXT and actual in {
        TYPE_TEXT,
        TYPE_NUMBER,
        TYPE_LOGICAL,
        TYPE_DATE,
        TYPE_DATETIME,
        TYPE_WEEKDAY,
        TYPE_NULL,
        TYPE_ANY,
        TYPE_UNKNOWN,
    }:
        return
    if not _is_assignable(actual, expected):
        _fail(
            "expression.type_mismatch",
            f"A expressão do parâmetro {param_name} produz {actual}, esperado {expected}.",
            argument=param_name,
            expected=expected,
            received=actual,
            expressionPath=path or param_name,
        )
