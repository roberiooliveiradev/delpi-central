"""Mutações estruturais determinísticas de scripts M DELPI."""

from __future__ import annotations

import json
from dataclasses import replace
from typing import Any, Mapping

from tv_app.application.services.data.m_query.m_compiler import (
    MCompileRequest,
    MCompileResult,
    MQueryCompiler,
)
from tv_app.application.services.data.m_query.m_formatter import (
    format_m_document,
    format_transform_plan_as_m,
)
from tv_app.application.services.data.m_query.m_legacy_adapter import legacy_steps_to_plan
from tv_app.application.services.data.m_query.m_parser import parse_m_script
from tv_app.domain.data_query.m_ast import (
    MBinaryExpression,
    MBinding,
    MCallExpression,
    MDocument,
    MEachExpression,
    MExpression,
    MFunctionExpression,
    MIdentifier,
    MIfExpression,
    MLetExpression,
    MListExpression,
    MParenthesizedExpression,
    MRecordExpression,
    MRecordField,
    MUnaryExpression,
)


class MMutationError(ValueError):
    """Comando de mutação inválido ou incompatível com o documento."""


_M_KEYWORDS = frozenset(
    {
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
)


def _m_text(value: Any) -> str:
    return '"' + str(value).replace('"', '""').replace("\r\n", "\n").replace("\r", "\n") + '"'


def _m_value(value: Any) -> str:
    if value is None:
        return "null"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return json.dumps(value, allow_nan=False)
    return _m_text(value)


def _m_identifier(value: str) -> str:
    if value.isidentifier() and value.casefold() not in _M_KEYWORDS:
        return value
    return f'#"{value.replace(chr(34), chr(34) * 2)}"'


def _required_text(arguments: Mapping[str, Any], field: str) -> str:
    value = arguments.get(field)
    if not isinstance(value, str) or not value.strip():
        raise MMutationError(f"{field} exige texto.")
    return value.strip()


def _m_text_list(values: Any, field: str) -> str:
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(item, str) and item.strip() for item in values)
    ):
        raise MMutationError(f"{field} exige uma lista não vazia de textos.")
    return "{" + ", ".join(_m_text(item.strip()) for item in values) + "}"


def _m_literal_list(values: Any, field: str) -> str:
    if (
        not isinstance(values, list)
        or not values
        or not all(
            item is None or isinstance(item, (str, int, float, bool))
            for item in values
        )
    ):
        raise MMutationError(f"{field} exige uma lista não vazia de valores escalares.")
    return "{" + ", ".join(_m_value(item) for item in values) + "}"


_SAFE_COLUMN_FUNCTIONS = {
    "trim": ("Text.Trim", "type text"),
    "clean": ("Text.Clean", "type text"),
    "upper": ("Text.Upper", "type text"),
    "lower": ("Text.Lower", "type text"),
    "proper": ("Text.Proper", "type text"),
    "length": ("Text.Length", "type number"),
    "contains": ("Text.Contains", "type logical"),
    "before_delimiter": ("Text.BeforeDelimiter", "type text"),
    "after_delimiter": ("Text.AfterDelimiter", "type text"),
    "between_delimiters": ("Text.BetweenDelimiters", "type text"),
    "abs": ("Number.Abs", "type number"),
    "round": ("Number.Round", "type number"),
    "round_up": ("Number.RoundUp", "type number"),
    "round_down": ("Number.RoundDown", "type number"),
    "mod": ("Number.Mod", "type number"),
    "date_year": ("Date.Year", "type number"),
    "date_month": ("Date.Month", "type number"),
    "date_day": ("Date.Day", "type number"),
    "date_start_of_month": ("Date.StartOfMonth", "type date"),
    "date_end_of_month": ("Date.EndOfMonth", "type date"),
    "date_add_days": ("Date.AddDays", "type date"),
    "date_add_months": ("Date.AddMonths", "type date"),
    "duration_days": ("Duration.Days", "type number"),
}
_SAFE_COLUMN_TYPES = {"any", "text", "number", "logical", "date", "datetime", "duration"}


def _expression_from_text(text: str) -> MExpression:
    wrapped = f"let\n    __mutacao = {text}\nin\n    __mutacao"
    return parse_m_script(wrapped).expression.bindings[0].expression


def _replace_identifier(expression: MExpression, old: str, new: str) -> MExpression:
    if isinstance(expression, MIdentifier):
        return replace(expression, name=new) if expression.name == old else expression
    if isinstance(expression, MCallExpression):
        return replace(
            expression,
            arguments=tuple(_replace_identifier(item, old, new) for item in expression.arguments),
        )
    if isinstance(expression, MListExpression):
        return replace(
            expression,
            items=tuple(_replace_identifier(item, old, new) for item in expression.items),
        )
    if isinstance(expression, MRecordExpression):
        return replace(
            expression,
            fields=tuple(
                replace(field, value=_replace_identifier(field.value, old, new))
                for field in expression.fields
            ),
        )
    if isinstance(expression, MEachExpression):
        return replace(expression, body=_replace_identifier(expression.body, old, new))
    if isinstance(expression, MIfExpression):
        return replace(
            expression,
            condition=_replace_identifier(expression.condition, old, new),
            then_value=_replace_identifier(expression.then_value, old, new),
            else_value=_replace_identifier(expression.else_value, old, new),
        )
    if isinstance(expression, MBinaryExpression):
        return replace(
            expression,
            left=_replace_identifier(expression.left, old, new),
            right=_replace_identifier(expression.right, old, new),
        )
    if isinstance(expression, MUnaryExpression):
        return replace(expression, operand=_replace_identifier(expression.operand, old, new))
    if isinstance(expression, MParenthesizedExpression):
        return replace(
            expression,
            expression=_replace_identifier(expression.expression, old, new),
        )
    if isinstance(expression, MFunctionExpression):
        return replace(expression, body=_replace_identifier(expression.body, old, new))
    return expression


def _legacy_step(operation: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
    aliases = {
        "rename_column": "rename",
        "select_columns": "select",
        "remove_columns": "select",
        "filter_rows": "filter",
        "add_column": "addColumn",
        "replace_value": "replace",
        "sort_rows": "sort",
        "keep_rows": "keepRows",
        "remove_rows": "removeRows",
        "change_type": "changeType",
        "fill_down": "fillDown",
        "promote_headers": "firstRowAsHeader",
        "group_by": "groupBy",
    }
    op = aliases.get(operation, operation)
    payload = {"op": op, **dict(arguments)}
    if op == "rename":
        payload["from"] = arguments.get("from", arguments.get("column"))
        payload["to"] = arguments.get("to", arguments.get("newName"))
    elif op == "filter":
        payload["cmp"] = arguments.get("cmp", arguments.get("operator", "eq"))
    elif op == "replace":
        payload["find"] = arguments.get("find", arguments.get("value"))
        payload["replaceWith"] = arguments.get("replaceWith", arguments.get("replacement", ""))
    elif op == "changeType":
        payload["to"] = arguments.get("to", arguments.get("type", "string"))
    elif op == "select" and operation == "remove_columns":
        remaining = arguments.get("remainingColumns")
        if not isinstance(remaining, list):
            raise MMutationError("remove_columns exige remainingColumns.")
        payload["columns"] = remaining
    return payload


def _insert_expression(operation: str, arguments: Mapping[str, Any], input_name: str) -> MExpression:
    source = _m_identifier(input_name)
    column = str(arguments.get("column") or "")
    direct: str | None = None
    if operation == "remove_columns":
        direct = f"Table.RemoveColumns({source}, {_m_text_list(arguments.get('columns'), 'columns')})"
    elif operation == "changeType":
        target = str(arguments.get("to") or "text")
        if target not in _SAFE_COLUMN_TYPES or not column:
            raise MMutationError("changeType exige coluna e tipo permitidos.")
        direct = (
            f"Table.TransformColumnTypes({source}, "
            f"{{{{{_m_text(column)}, type {target}}}}}, \"pt-BR\")"
        )
    elif operation == "reorder_columns":
        direct = f"Table.ReorderColumns({source}, {_m_text_list(arguments.get('columns'), 'columns')})"
    elif operation == "duplicate_column":
        direct = (
            f"Table.DuplicateColumn({source}, {_m_text(_required_text(arguments, 'column'))}, "
            f"{_m_text(_required_text(arguments, 'newName'))})"
        )
    elif operation == "split_column":
        delimiter = str(arguments.get("delimiter") or "")
        if not delimiter:
            raise MMutationError("split_column exige delimiter.")
        direct = (
            f"Table.SplitColumn({source}, {_m_text(column)}, "
            f"Splitter.SplitTextByDelimiter({_m_text(delimiter)}, QuoteStyle.Csv), "
            f"{_m_text_list(arguments.get('newColumns'), 'newColumns')})"
        )
    elif operation == "add_index":
        new_name = str(arguments.get("newName") or "Índice").strip() or "Índice"
        direct = (
            f"Table.AddIndexColumn({source}, {_m_text(new_name)}, "
            f"{_m_value(arguments.get('initial', 0))}, {_m_value(arguments.get('increment', 1))}, type number)"
        )
    elif operation == "distinct_rows":
        columns = arguments.get("columns")
        direct = (
            f"Table.Distinct({source}, {_m_text_list(columns, 'columns')})"
            if columns
            else f"Table.Distinct({source})"
        )
    elif operation == "range_rows":
        count = arguments.get("count")
        direct = f"Table.Range({source}, {_m_value(arguments.get('offset', 0))}"
        direct += f", {_m_value(count)})" if count is not None else ")"
    elif operation == "fill_up":
        direct = f"Table.FillUp({source}, {_m_text_list(arguments.get('columns') or [column], 'columns')})"
    elif operation == "transpose":
        direct = f"Table.Transpose({source})"
    elif operation == "reverse_rows":
        direct = f"Table.ReverseRows({source})"
    elif operation == "append_queries":
        queries = arguments.get("queries")
        if (
            not isinstance(queries, list)
            or not queries
            or not all(isinstance(item, str) and item.strip() for item in queries)
        ):
            raise MMutationError("append_queries exige queries.")
        references = [
            source,
            *(_m_identifier(item.strip()) for item in queries if item.strip() != input_name),
        ]
        direct = f"Table.Combine({{{', '.join(references)}}})"
    elif operation == "transform_column":
        function_key = str(arguments.get("function") or "")
        spec = _SAFE_COLUMN_FUNCTIONS.get(function_key)
        if spec is None or not column:
            raise MMutationError("Função de coluna não permitida.")
        function_name, target_type = spec
        extra = arguments.get("arguments") or []
        if not isinstance(extra, list):
            raise MMutationError("arguments deve ser uma lista.")
        rendered = ", ".join(["_", *(_m_value(item) for item in extra)])
        direct = (
            f"Table.TransformColumns({source}, "
            f"{{{{{_m_text(column)}, each {function_name}({rendered}), {target_type}}}}})"
        )
    elif operation == "add_custom_column":
        name = str(arguments.get("newName") or "")
        expression = str(arguments.get("expression") or "").strip()
        target = str(arguments.get("type") or "any")
        if target not in _SAFE_COLUMN_TYPES:
            raise MMutationError("Tipo de coluna personalizada inválido.")
        if not name or not expression:
            raise MMutationError("Nome e expressão são obrigatórios.")
        direct = f"Table.AddColumn({source}, {_m_text(name)}, each {expression}, type {target})"
    elif operation == "add_conditional_column":
        name = str(arguments.get("newName") or "")
        operator = str(arguments.get("operator") or "=")
        operator = {"eq": "=", "neq": "<>", "gt": ">", "gte": ">=", "lt": "<", "lte": "<="}.get(operator, operator)
        if operator not in {"=", "<>", ">", ">=", "<", "<="} or not name or not column:
            raise MMutationError("Condição inválida.")
        direct = (
            f"Table.AddColumn({source}, {_m_text(name)}, each if [{_m_identifier(column)}] "
            f"{operator} {_m_value(arguments.get('value'))} then {_m_value(arguments.get('thenValue'))} "
            f"else {_m_value(arguments.get('elseValue'))})"
        )
    elif operation == "remove_errors":
        columns = arguments.get("columns") or ([column] if column else [])
        direct = f"Table.RemoveRowsWithErrors({source}, {_m_text_list(columns, 'columns')})"
    elif operation == "replace_errors":
        direct = (
            f"Table.ReplaceErrorValues({source}, "
            f"{{{{{_m_text(column)}, {_m_value(arguments.get('replacement'))}}}}})"
        )
    elif operation == "group_rows":
        keys = _m_text_list(arguments.get("keys"), "keys")
        output = str(arguments.get("output") or "Resultado")
        aggregate = str(arguments.get("aggregate") or "sum")
        aggregate_fn = {
            "sum": "List.Sum",
            "average": "List.Average",
            "min": "List.Min",
            "max": "List.Max",
            "count": "List.Count",
        }.get(aggregate)
        value_column = str(arguments.get("valueColumn") or "")
        if aggregate_fn is None or not value_column:
            raise MMutationError("Agregação inválida.")
        direct = (
            f"Table.Group({source}, {keys}, "
            f"{{{{{_m_text(output)}, each {aggregate_fn}([{_m_identifier(value_column)}]), type number}}}})"
        )
    elif operation == "pivot":
        attribute_column = _required_text(arguments, "attributeColumn")
        value_column = _required_text(arguments, "valueColumn")
        direct = (
            f"Table.Pivot({source}, {_m_literal_list(arguments.get('values'), 'values')}, "
            f"{_m_text(attribute_column)}, {_m_text(value_column)}, List.Sum)"
        )
    elif operation == "unpivot":
        direct = (
            f"Table.Unpivot({source}, {_m_text_list(arguments.get('columns'), 'columns')}, "
            f"{_m_text(arguments.get('attributeName') or 'Atributo')}, "
            f"{_m_text(arguments.get('valueName') or 'Valor')})"
        )
    elif operation == "nested_join":
        query = _required_text(arguments, "query")
        nested_column = str(arguments.get("newColumn") or query).strip() or query
        direct = (
            f"Table.NestedJoin({source}, {_m_text_list(arguments.get('leftKeys'), 'leftKeys')}, "
            f"{_m_identifier(query)}, {_m_text_list(arguments.get('rightKeys'), 'rightKeys')}, "
            f"{_m_text(nested_column)}, JoinKind.LeftOuter)"
        )
    elif operation == "expand_table_column":
        aliases = arguments.get("newColumnNames")
        direct = (
            f"Table.ExpandTableColumn({source}, {_m_text(_required_text(arguments, 'column'))}, "
            f"{_m_text_list(arguments.get('columns'), 'columns')}"
            + (f", {_m_text_list(aliases, 'newColumnNames')}" if aliases else "")
            + ")"
        )
    if direct is not None:
        return _expression_from_text(direct)
    plan = legacy_steps_to_plan({"steps": [_legacy_step(operation, arguments)]})
    if plan is None:
        raise MMutationError("Operação ou argumentos de inserção inválidos.")
    generated = parse_m_script(format_transform_plan_as_m(plan))
    expression = generated.expression.bindings[0].expression
    return _replace_identifier(expression, "Fonte", input_name)


def _unique_name(bindings: tuple[MBinding, ...], preferred: str) -> str:
    existing = {binding.name for binding in bindings}
    if preferred not in existing:
        return preferred
    suffix = 2
    while f"{preferred} {suffix}" in existing:
        suffix += 1
    return f"{preferred} {suffix}"


class MQueryMutationService:
    def __init__(self, compiler: MQueryCompiler | None = None) -> None:
        self._compiler = compiler or MQueryCompiler()

    def mutate(
        self,
        request: MCompileRequest,
        action: Mapping[str, Any],
    ) -> MCompileResult:
        kind = str(action.get("type") or "").strip()
        if kind == "convert_legacy":
            plan = legacy_steps_to_plan({"steps": action.get("legacySteps") or []})
            script = (
                format_transform_plan_as_m(plan)
                if plan is not None
                else "let\n    FonteSemEtapas = Table.Skip(Fonte, 0)\nin\n    FonteSemEtapas"
            )
            return self._compiler.compile(replace(request, script=script))
        document = parse_m_script(request.script)
        bindings = document.expression.bindings
        output = document.expression.output

        if kind == "format_script":
            pass
        elif kind == "insert_step":
            after = str(action.get("afterStepName") or "").strip()
            operation = str(action.get("operation") or "").strip()
            arguments = action.get("arguments")
            args = arguments if isinstance(arguments, Mapping) else {}
            position = len(bindings)
            input_name = "Fonte"
            if after:
                position = next(
                    (index + 1 for index, binding in enumerate(bindings) if binding.name == after),
                    -1,
                )
                if position < 0:
                    raise MMutationError("Etapa de inserção não encontrada.")
                input_name = after
            elif bindings:
                input_name = bindings[-1].name
            preferred = str(action.get("stepName") or args.get("stepName") or operation).strip()
            name = _unique_name(bindings, preferred or "Etapa")
            expression = _insert_expression(operation, args, input_name)
            item = MBinding(expression.source_range, name, expression, quoted=True)
            trailing = bindings[position:]
            if trailing and after:
                trailing = tuple(
                    replace(
                        binding,
                        expression=_replace_identifier(binding.expression, after, name),
                    )
                    for binding in trailing
                )
                output = _replace_identifier(output, after, name)
            else:
                output = MIdentifier(item.source_range, name, quoted=True)
            bindings = (*bindings[:position], item, *trailing)
        elif kind == "replace_step_expression":
            name = str(action.get("stepName") or "").strip()
            expression_text = str(action.get("expression") or "").strip()
            if not name or not expression_text:
                raise MMutationError("Etapa e expressão são obrigatórias.")
            expression = _expression_from_text(expression_text)
            found = False
            updated: list[MBinding] = []
            for binding in bindings:
                if binding.name == name:
                    updated.append(replace(binding, expression=expression))
                    found = True
                else:
                    updated.append(binding)
            if not found:
                raise MMutationError("Etapa não encontrada.")
            bindings = tuple(updated)
        elif kind in {"rename_step", "rename_query"}:
            old = str(action.get("stepName") or action.get("from") or "").strip()
            new = str(action.get("newName") or action.get("to") or "").strip()
            if not old or not new:
                raise MMutationError("Nome atual e novo nome são obrigatórios.")
            if kind == "rename_step":
                if any(binding.name == new for binding in bindings):
                    raise MMutationError("Já existe uma etapa com esse nome.")
                if not any(binding.name == old for binding in bindings):
                    raise MMutationError("Etapa não encontrada.")
                bindings = tuple(
                    replace(
                        binding,
                        name=new if binding.name == old else binding.name,
                        expression=_replace_identifier(binding.expression, old, new),
                    )
                    for binding in bindings
                )
            else:
                bindings = tuple(
                    replace(binding, expression=_replace_identifier(binding.expression, old, new))
                    for binding in bindings
                )
            output = _replace_identifier(output, old, new)
        elif kind == "move_step":
            name = str(action.get("stepName") or "").strip()
            target = int(action.get("targetIndex", -1))
            current = next(
                (index for index, binding in enumerate(bindings) if binding.name == name),
                -1,
            )
            if current < 0 or target < 0 or target >= len(bindings):
                raise MMutationError("Posição de etapa inválida.")
            reordered = list(bindings)
            item = reordered.pop(current)
            reordered.insert(target, item)
            bindings = tuple(reordered)
        elif kind == "remove_step":
            name = str(action.get("stepName") or "").strip()
            removed = next((binding for binding in bindings if binding.name == name), None)
            if removed is None:
                raise MMutationError("Etapa não encontrada.")
            if not isinstance(removed.expression, MCallExpression) or not removed.expression.arguments:
                raise MMutationError("A etapa não possui uma entrada substituível.")
            replacement = removed.expression.arguments[0]
            if not isinstance(replacement, MIdentifier):
                raise MMutationError("A etapa possui dependência composta e não pode ser removida.")
            bindings = tuple(
                replace(
                    binding,
                    expression=_replace_identifier(binding.expression, name, replacement.name),
                )
                for binding in bindings
                if binding.name != name
            )
            output = _replace_identifier(output, name, replacement.name)
        else:
            raise MMutationError("Ação de mutação M não suportada.")

        expression = replace(document.expression, bindings=bindings, output=output)
        mutated = replace(document, expression=expression)
        canonical = format_m_document(mutated)
        return self._compiler.compile(replace(request, script=canonical))
