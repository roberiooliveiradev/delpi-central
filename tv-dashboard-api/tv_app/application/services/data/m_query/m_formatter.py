"""Formatter v1 legado → script M canônico, sem parser ou execução M."""

from __future__ import annotations

import ast
import re

from tv_app.domain.data_query.m_ast import (
    MBinaryExpression,
    MCallExpression,
    MDocument,
    MEachExpression,
    MExpression,
    MFieldAccess,
    MFunctionExpression,
    MIdentifier,
    MIfExpression,
    MListExpression,
    MLiteral,
    MParenthesizedExpression,
    MRecordExpression,
    MTypeExpression,
    MUnaryExpression,
)
from tv_app.domain.data_query.transform_plan import (
    AddColumnStep,
    ChangeTypeStep,
    FillDownStep,
    FilterStep,
    GroupByStep,
    MergeStep,
    PivotStep,
    PromoteHeadersStep,
    RenameStep,
    ReplaceStep,
    RowCountStep,
    SelectStep,
    SortStep,
    TransformOperation,
    TransformPlan,
    UnpivotStep,
)

_SIMPLE_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_AGGREGATION_FUNCTIONS = {
    "sum": "List.Sum",
    "avg": "List.Average",
    "min": "List.Min",
    "max": "List.Max",
    "count": "List.Count",
    "first": "List.First",
}


def _m_string(value: object) -> str:
    text = str(value).replace('"', '""').replace("\r\n", "\n").replace("\r", "\n")
    return f'"{text}"'


def _m_literal(value: object) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)):
        return repr(value)
    return _m_string(value)


def _quoted_identifier(value: str) -> str:
    escaped = value.replace('"', '""')
    return value if _SIMPLE_IDENTIFIER.fullmatch(value) else f'#"{escaped}"'


def _step_reference(value: str) -> str:
    return value if value == "Fonte" else _quoted_identifier(value)


def _field_reference(value: str) -> str:
    return f"[{_quoted_identifier(value)}]"


def _legacy_expression_to_m(expression: str) -> str:
    """Traduz a DSL legada já permitida; não interpreta entrada M."""

    rewritten = re.sub(r"\bif\s*\(", "iff(", expression, flags=re.IGNORECASE)
    try:
        tree = ast.parse(rewritten, mode="eval")
    except SyntaxError:
        return "null /* expressão legada inválida */"

    def render(node: ast.AST) -> str:
        if isinstance(node, ast.Expression):
            return render(node.body)
        if isinstance(node, ast.Constant):
            return _m_literal(node.value)
        if isinstance(node, ast.Name):
            return _field_reference(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return f"-{render(node.operand)}"
        if isinstance(node, ast.BinOp):
            operators = {
                ast.Add: "+",
                ast.Sub: "-",
                ast.Mult: "*",
                ast.Div: "/",
            }
            symbol = operators.get(type(node.op))
            if symbol is None:
                raise ValueError("Operador legado não suportado.")
            return f"({render(node.left)} {symbol} {render(node.right)})"
        if isinstance(node, ast.Compare) and len(node.ops) == len(node.comparators) == 1:
            operators = {
                ast.Eq: "=",
                ast.NotEq: "<>",
                ast.Gt: ">",
                ast.GtE: ">=",
                ast.Lt: "<",
                ast.LtE: "<=",
            }
            symbol = operators.get(type(node.ops[0]))
            if symbol is None:
                raise ValueError("Comparador legado não suportado.")
            return f"({render(node.left)} {symbol} {render(node.comparators[0])})"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            arguments = [render(argument) for argument in node.args]
            name = node.func.id
            if name == "iff" and len(arguments) == 3:
                return f"if {arguments[0]} then {arguments[1]} else {arguments[2]}"
            function_map = {
                "concat": "Text.Combine",
                "abs": "Number.Abs",
                "min": "List.Min",
                "max": "List.Max",
                "len": "Text.Length",
                "lower": "Text.Lower",
                "upper": "Text.Upper",
                "trim": "Text.Trim",
            }
            if name == "coalesce":
                return f"List.First(List.RemoveNulls({{{', '.join(arguments)}}}), null)"
            target = function_map.get(name)
            if target is None:
                raise ValueError("Função legada não suportada.")
            if name in {"concat", "min", "max"}:
                return f"{target}({{{', '.join(arguments)}}})"
            return f"{target}({', '.join(arguments)})"
        raise ValueError("Expressão legada não suportada.")

    try:
        return render(tree)
    except ValueError:
        return "null /* expressão legada não suportada */"


def _format_step_expression(step: object) -> str:
    source = _step_reference(step.input_name)  # type: ignore[attr-defined]
    if isinstance(step, RenameStep):
        return (
            f"Table.RenameColumns({source}, "
            f"{{{{{_m_string(step.source_column)}, {_m_string(step.target_column)}}}}})"
        )
    if isinstance(step, SelectStep):
        return f"Table.SelectColumns({source}, {{{', '.join(map(_m_string, step.columns))}}})"
    if isinstance(step, FilterStep):
        field = _field_reference(step.column)
        predicates = {
            "eq": f"{field} = {_m_literal(step.value)}",
            "neq": f"{field} <> {_m_literal(step.value)}",
            "gt": f"{field} > {_m_literal(step.value)}",
            "lt": f"{field} < {_m_literal(step.value)}",
            "notNull": f"{field} <> null",
            "contains": f"Text.Contains(Text.From({field}), {_m_literal(step.value)})",
            "startsWith": f"Text.StartsWith(Text.From({field}), {_m_literal(step.value)})",
        }
        return f"Table.SelectRows({source}, each {predicates[step.comparator]})"
    if isinstance(step, AddColumnStep):
        return (
            f"Table.AddColumn({source}, {_m_string(step.column)}, "
            f"each {_legacy_expression_to_m(step.legacy_expression)})"
        )
    if isinstance(step, ReplaceStep):
        return (
            f"Table.ReplaceValue({source}, {_m_string(step.find)}, "
            f"{_m_string(step.replacement)}, Replacer.ReplaceText, "
            f"{{{_m_string(step.column)}}})"
        )
    if isinstance(step, SortStep):
        order = "Order.Descending" if step.direction == "desc" else "Order.Ascending"
        return f"Table.Sort({source}, {{{{{_m_string(step.column)}, {order}}}}})"
    if isinstance(step, RowCountStep):
        if step.operation == TransformOperation.KEEP_ROWS:
            function = "Table.LastN" if step.from_end else "Table.FirstN"
        else:
            function = "Table.RemoveLastN" if step.from_end else "Table.Skip"
        return f"{function}({source}, {step.count})"
    if isinstance(step, ChangeTypeStep):
        target = "type number" if step.target_type == "number" else "type text"
        return (
            f"Table.TransformColumnTypes({source}, "
            f"{{{{{_m_string(step.column)}, {target}}}}})"
        )
    if isinstance(step, FillDownStep):
        return f"Table.FillDown({source}, {{{_m_string(step.column)}}})"
    if isinstance(step, PromoteHeadersStep):
        return f"Table.PromoteHeaders({source}, [PromoteAllScalars = true])"
    if isinstance(step, GroupByStep):
        keys = ", ".join(map(_m_string, step.keys))
        aggregations = ", ".join(
            (
                "{"
                f"{_m_string(item.output_column)}, "
                f"each {_AGGREGATION_FUNCTIONS[item.function]}({_field_reference(item.column)})"
                "}"
            )
            for item in step.aggregations
        )
        return f"Table.Group({source}, {{{keys}}}, {{{aggregations}}})"
    if isinstance(step, PivotStep):
        aggregation = _AGGREGATION_FUNCTIONS[step.aggregation]
        return (
            f"Table.Pivot({source}, "
            f"List.Distinct(Table.Column({source}, {_m_string(step.column)})), "
            f"{_m_string(step.column)}, {_m_string(step.value_column)}, {aggregation})"
        )
    if isinstance(step, UnpivotStep):
        return (
            f"Table.Unpivot({source}, {{{', '.join(map(_m_string, step.columns))}}}, "
            f"{_m_string(step.name_column)}, {_m_string(step.value_column)})"
        )
    if isinstance(step, MergeStep):
        nested = (
            f"Table.NestedJoin({source}, {{{_m_string(step.left_key)}}}, "
            f"{_quoted_identifier(step.source_id)}, {{{_m_string(step.right_key)}}}, "
            f'"__merge", JoinKind.LeftOuter)'
        )
        columns = ", ".join(map(_m_string, step.columns))
        return (
            f"Table.ExpandTableColumn({nested}, \"__merge\", "
            f"{{{columns}}}, {{{columns}}})"
        )
    raise TypeError(f"Etapa não suportada: {type(step).__name__}")


def format_transform_plan_as_m(plan: TransformPlan) -> str:
    bindings = [
        f"    {_quoted_identifier(step.name)} = {_format_step_expression(step)}"
        for step in plan.steps
    ]
    return "let\n" + ",\n".join(bindings) + f"\nin\n    {_step_reference(plan.output)}"


_M_KEYWORDS = {
    "and",
    "each",
    "else",
    "false",
    "if",
    "in",
    "let",
    "not",
    "null",
    "or",
    "then",
    "true",
    "type",
}
_PRECEDENCE = {
    "or": 1,
    "and": 2,
    "=": 3,
    "<>": 3,
    "<": 3,
    "<=": 3,
    ">": 3,
    ">=": 3,
    "&": 4,
    "+": 5,
    "-": 5,
    "*": 6,
    "/": 6,
}


def _canonical_identifier(value: str) -> str:
    if value != "#shared" and value.isidentifier() and value.casefold() not in _M_KEYWORDS:
        return value
    return f'#"{value.replace(chr(34), chr(34) * 2)}"'


def _format_expression(expression: MExpression, parent_precedence: int = 0) -> str:
    if isinstance(expression, MIdentifier):
        if "." in expression.name and not expression.quoted:
            return ".".join(_canonical_identifier(part) for part in expression.name.split("."))
        return _canonical_identifier(expression.name)
    if isinstance(expression, MLiteral):
        return _m_literal(expression.value)
    if isinstance(expression, MTypeExpression):
        return f"type {expression.name}"
    if isinstance(expression, MFieldAccess):
        return f"[{_canonical_identifier(expression.field_name)}]"
    if isinstance(expression, MListExpression):
        return "{" + ", ".join(_format_expression(item) for item in expression.items) + "}"
    if isinstance(expression, MRecordExpression):
        fields = ", ".join(
            f"{_canonical_identifier(field.name)} = {_format_expression(field.value)}"
            for field in expression.fields
        )
        return f"[{fields}]"
    if isinstance(expression, MCallExpression):
        arguments = ", ".join(_format_expression(item) for item in expression.arguments)
        return f"{expression.function_name}({arguments})"
    if isinstance(expression, MEachExpression):
        return f"each {_format_expression(expression.body)}"
    if isinstance(expression, MIfExpression):
        return (
            f"if {_format_expression(expression.condition)} "
            f"then {_format_expression(expression.then_value)} "
            f"else {_format_expression(expression.else_value)}"
        )
    if isinstance(expression, MUnaryExpression):
        rendered = f"{expression.operator} {_format_expression(expression.operand, 7)}"
        return f"({rendered})" if parent_precedence > 7 else rendered
    if isinstance(expression, MBinaryExpression):
        precedence = _PRECEDENCE[expression.operator]
        rendered = (
            f"{_format_expression(expression.left, precedence)} {expression.operator} "
            f"{_format_expression(expression.right, precedence + 1)}"
        )
        return f"({rendered})" if precedence < parent_precedence else rendered
    if isinstance(expression, MParenthesizedExpression):
        return _format_expression(expression.expression, parent_precedence)
    if isinstance(expression, MFunctionExpression):
        parameters = ", ".join(_canonical_identifier(item) for item in expression.parameters)
        return f"({parameters}) => {_format_expression(expression.body)}"
    raise TypeError(f"Nó M não suportado: {type(expression).__name__}")


def format_m_document(document: MDocument) -> str:
    """Formata AST M de modo determinístico e idempotente."""

    bindings = [
        f"    {_canonical_identifier(binding.name)} = {_format_expression(binding.expression)}"
        for binding in document.expression.bindings
    ]
    output = _format_expression(document.expression.output)
    return "let\n" + ",\n".join(bindings) + f"\nin\n    {output}"


def format_m_expression(expression: MExpression) -> str:
    """Formata uma expressão isolada para consumidores server-driven."""

    return _format_expression(expression)
