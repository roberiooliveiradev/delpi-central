"""Mutações estruturais determinísticas de scripts M DELPI."""

from __future__ import annotations

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
