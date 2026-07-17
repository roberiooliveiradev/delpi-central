"""Análise semântica deny-by-default do perfil M DELPI v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tv_app.application.services.data.m_query.m_function_registry import (
    MFunctionRegistry,
    get_function_registry,
)
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
from tv_app.domain.data_query.m_diagnostics import Diagnostic, DiagnosticSeverity

_ALLOWED_QUALIFIED_SYMBOLS = {
    "Order.Ascending",
    "Order.Descending",
    "Replacer.ReplaceText",
    "Replacer.ReplaceValue",
    "JoinKind.LeftOuter",
}


@dataclass(frozen=True, slots=True)
class SemanticAnalysis:
    diagnostics: tuple[Diagnostic, ...]
    referenced_queries: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return not any(item.severity == DiagnosticSeverity.ERROR for item in self.diagnostics)


def expression_children(expression: MExpression) -> tuple[MExpression, ...]:
    if isinstance(expression, MListExpression):
        return expression.items
    if isinstance(expression, MRecordExpression):
        return tuple(field.value for field in expression.fields)
    if isinstance(expression, MCallExpression):
        return expression.arguments
    if isinstance(expression, MEachExpression):
        return (expression.body,)
    if isinstance(expression, MIfExpression):
        return (expression.condition, expression.then_value, expression.else_value)
    if isinstance(expression, MBinaryExpression):
        return (expression.left, expression.right)
    if isinstance(expression, MUnaryExpression):
        return (expression.operand,)
    if isinstance(expression, MParenthesizedExpression):
        return (expression.expression,)
    if isinstance(expression, MFunctionExpression):
        return (expression.body,)
    return ()


def ast_metrics(document: MDocument) -> tuple[int, int]:
    count = 0
    maximum_depth = 0
    stack: list[tuple[object, int]] = [(document, 1)]
    while stack:
        node, depth = stack.pop()
        count += 1
        maximum_depth = max(maximum_depth, depth)
        if isinstance(node, MDocument):
            stack.append((node.expression, depth + 1))
        elif hasattr(node, "bindings") and hasattr(node, "output"):
            stack.extend((binding, depth + 1) for binding in node.bindings)
            stack.append((node.output, depth + 1))
        elif hasattr(node, "expression") and not isinstance(node, MExpression.__args__):
            stack.append((node.expression, depth + 1))
        elif isinstance(node, MExpression.__args__):
            stack.extend((child, depth + 1) for child in expression_children(node))
    return count, maximum_depth


def _error(code: str, message: str, node: object, hint: str | None = None) -> Diagnostic:
    return Diagnostic(
        code=code,
        severity=DiagnosticSeverity.ERROR,
        message=message,
        source_range=getattr(node, "source_range", None),
        hint=hint,
    )


def _literal_strings(expression: MExpression) -> tuple[str, ...] | None:
    if not isinstance(expression, MListExpression):
        return None
    values: list[str] = []
    for item in expression.items:
        if not isinstance(item, MLiteral) or not isinstance(item.value, str):
            return None
        values.append(item.value)
    return tuple(values)


def _rename_pairs(expression: MExpression) -> tuple[tuple[str, str], ...] | None:
    if not isinstance(expression, MListExpression):
        return None
    pairs: list[tuple[str, str]] = []
    for item in expression.items:
        values = _literal_strings(item)
        if values is None or len(values) != 2:
            return None
        pairs.append((values[0], values[1]))
    return tuple(pairs)


class MSemanticAnalyzer:
    def __init__(self, registry: MFunctionRegistry | None = None) -> None:
        self.registry = registry or get_function_registry()

    def analyze(
        self,
        document: MDocument,
        *,
        source_columns: Iterable[str] | None = None,
        query_bindings: Iterable[str] = (),
    ) -> SemanticAnalysis:
        diagnostics: list[Diagnostic] = []
        query_names = {str(name) for name in query_bindings}
        known_tables: dict[str, set[str] | None] = {
            "Fonte": None if source_columns is None else set(source_columns),
            **{name: None for name in query_names},
        }
        referenced_queries: set[str] = set()
        seen_bindings: set[str] = set()
        user_functions = {
            binding.name
            for binding in document.expression.bindings
            if isinstance(binding.expression, MFunctionExpression)
        }

        for binding in document.expression.bindings:
            if binding.name == "Fonte":
                diagnostics.append(
                    _error("m.reserved_identifier", "Fonte é um identificador reservado.", binding)
                )
            if binding.name in seen_bindings:
                diagnostics.append(
                    _error(
                        "m.duplicate_binding",
                        f'A etapa "{binding.name}" foi declarada mais de uma vez.',
                        binding,
                    )
                )
                continue
            seen_bindings.add(binding.name)
            expression = binding.expression
            if isinstance(expression, MFunctionExpression):
                diagnostics.append(
                    _error(
                        "m.user_function_not_allowed",
                        "Funções definidas pelo usuário não são permitidas no M DELPI v1.",
                        expression,
                    )
                )
                continue
            if isinstance(expression, MIdentifier):
                self._validate_identifier(
                    expression,
                    known_tables,
                    query_names,
                    referenced_queries,
                    diagnostics,
                    current_binding=binding.name,
                )
                if expression.name in known_tables:
                    known_tables[binding.name] = known_tables[expression.name]
                continue
            if not isinstance(expression, MCallExpression):
                diagnostics.append(
                    _error(
                        "m.table_expression_required",
                        "Cada etapa deve produzir uma tabela por uma função Table.* permitida.",
                        expression,
                    )
                )
                continue

            spec = self.registry.resolve(expression.function_name)
            if spec is None or spec.kind != "transform":
                diagnostics.append(self._function_not_allowed(expression))
                self._validate_nested(
                    expression,
                    diagnostics,
                    known_columns=None,
                    user_functions=user_functions,
                )
                continue
            self._validate_arity(expression, spec.min_args, spec.max_args, diagnostics)
            if not expression.arguments or not isinstance(expression.arguments[0], MIdentifier):
                diagnostics.append(
                    _error(
                        "m.table_input_required",
                        "A primeira entrada da transformação deve ser uma etapa ou consulta autorizada.",
                        expression,
                    )
                )
                continue
            input_identifier = expression.arguments[0]
            self._validate_identifier(
                input_identifier,
                known_tables,
                query_names,
                referenced_queries,
                diagnostics,
                current_binding=binding.name,
            )
            input_columns = known_tables.get(input_identifier.name)
            self._collect_query_references(
                expression,
                query_names,
                referenced_queries,
            )
            for argument in expression.arguments[1:]:
                if (
                    expression.function_name == "Table.PromoteHeaders"
                    and isinstance(argument, MRecordExpression)
                ):
                    for field in argument.fields:
                        self._validate_nested(
                            field.value,
                            diagnostics,
                            known_columns=input_columns,
                            user_functions=user_functions,
                        )
                    continue
                self._validate_nested(
                    argument,
                    diagnostics,
                    known_columns=input_columns,
                    user_functions=user_functions,
                )
            self._validate_record_scope(expression, diagnostics)
            self._validate_function_shape(expression, diagnostics)
            known_tables[binding.name] = self._infer_columns(
                expression,
                input_columns,
                diagnostics,
            )

        output = document.expression.output
        if not isinstance(output, MIdentifier):
            diagnostics.append(
                _error("m.output_table_required", "A expressão in deve referenciar uma etapa.", output)
            )
        else:
            self._validate_identifier(
                output,
                known_tables,
                query_names,
                referenced_queries,
                diagnostics,
                current_binding=None,
            )
        return SemanticAnalysis(tuple(diagnostics), tuple(sorted(referenced_queries)))

    def _function_not_allowed(self, expression: MCallExpression) -> Diagnostic:
        return _error(
            "m.function_not_allowed",
            f"A função {expression.function_name} não é permitida no M DELPI v1.",
            expression,
            "Use somente funções publicadas em /data/m/functions.",
        )

    def _validate_arity(
        self,
        expression: MCallExpression,
        minimum: int,
        maximum: int,
        diagnostics: list[Diagnostic],
    ) -> None:
        count = len(expression.arguments)
        if count < minimum or count > maximum:
            diagnostics.append(
                _error(
                    "m.invalid_argument_count",
                    f"{expression.function_name} recebeu {count} argumento(s); esperado de {minimum} a {maximum}.",
                    expression,
                )
            )

    def _validate_identifier(
        self,
        identifier: MIdentifier,
        known_tables: dict[str, set[str] | None],
        query_names: set[str],
        referenced_queries: set[str],
        diagnostics: list[Diagnostic],
        *,
        current_binding: str | None,
    ) -> None:
        if identifier.name == "#shared":
            diagnostics.append(
                _error(
                    "m.identifier_not_allowed",
                    "#shared não é permitido no M DELPI v1.",
                    identifier,
                )
            )
        elif current_binding is not None and identifier.name == current_binding:
            diagnostics.append(
                _error(
                    "m.recursion_not_allowed",
                    "Recursão não é permitida no M DELPI v1.",
                    identifier,
                )
            )
        elif identifier.name not in known_tables:
            diagnostics.append(
                _error(
                    "m.unknown_identifier",
                    f'O identificador "{identifier.name}" não foi encontrado.',
                    identifier,
                )
            )
        elif identifier.name in query_names:
            referenced_queries.add(identifier.name)

    def _validate_nested(
        self,
        expression: MExpression,
        diagnostics: list[Diagnostic],
        *,
        known_columns: set[str] | None,
        user_functions: set[str],
    ) -> None:
        if isinstance(expression, MFunctionExpression):
            diagnostics.append(
                _error(
                    "m.user_function_not_allowed",
                    "Funções definidas pelo usuário não são permitidas no M DELPI v1.",
                    expression,
                )
            )
            return
        if isinstance(expression, MCallExpression):
            spec = self.registry.resolve(expression.function_name)
            if expression.function_name in user_functions:
                diagnostics.append(
                    _error(
                        "m.user_function_not_allowed",
                        "Chamadas a funções definidas pelo usuário não são permitidas.",
                        expression,
                    )
                )
            elif spec is None or spec.kind != "scalar":
                diagnostics.append(self._function_not_allowed(expression))
            else:
                self._validate_arity(expression, spec.min_args, spec.max_args, diagnostics)
        elif isinstance(expression, MIdentifier):
            if expression.name == "#shared":
                diagnostics.append(
                    _error("m.identifier_not_allowed", "#shared não é permitido.", expression)
                )
            elif (
                "." in expression.name
                and expression.name not in _ALLOWED_QUALIFIED_SYMBOLS
                and (
                    self.registry.resolve(expression.name) is None
                    or self.registry.resolve(expression.name).kind != "scalar"  # type: ignore[union-attr]
                )
            ):
                diagnostics.append(
                    _error(
                        "m.identifier_not_allowed",
                        f"O símbolo {expression.name} não é permitido.",
                        expression,
                    )
                )
        elif isinstance(expression, MFieldAccess):
            if known_columns is not None and expression.field_name not in known_columns:
                diagnostics.append(
                    _error(
                        "m.unknown_column",
                        f'A coluna "{expression.field_name}" não existe no schema informado.',
                        expression,
                    )
                )
        elif isinstance(expression, MRecordExpression):
            diagnostics.append(
                _error(
                    "m.record_not_allowed",
                    "Records só são aceitos nas opções de Table.PromoteHeaders.",
                    expression,
                )
            )
        for child in expression_children(expression):
            self._validate_nested(
                child,
                diagnostics,
                known_columns=known_columns,
                user_functions=user_functions,
            )

    @staticmethod
    def _collect_query_references(
        expression: MExpression,
        query_names: set[str],
        referenced_queries: set[str],
    ) -> None:
        stack = [expression]
        while stack:
            current = stack.pop()
            if isinstance(current, MIdentifier) and current.name in query_names:
                referenced_queries.add(current.name)
            stack.extend(expression_children(current))

    def _validate_record_scope(
        self,
        expression: MCallExpression,
        diagnostics: list[Diagnostic],
    ) -> None:
        for argument in expression.arguments:
            if isinstance(argument, MRecordExpression) and expression.function_name != "Table.PromoteHeaders":
                diagnostics.append(
                    _error(
                        "m.record_not_allowed",
                        "Records só são aceitos nas opções de Table.PromoteHeaders.",
                        argument,
                    )
                )
            if (
                expression.function_name == "Table.PromoteHeaders"
                and isinstance(argument, MRecordExpression)
                and any(field.name != "PromoteAllScalars" for field in argument.fields)
            ):
                diagnostics.append(
                    _error(
                        "m.record_field_not_allowed",
                        "Apenas PromoteAllScalars é permitido nas opções de cabeçalho.",
                        argument,
                    )
                )

    def _validate_function_shape(
        self,
        expression: MCallExpression,
        diagnostics: list[Diagnostic],
    ) -> None:
        arguments = expression.arguments
        name = expression.function_name
        if name in {"Table.FirstN", "Table.LastN", "Table.Skip", "Table.RemoveLastN"}:
            if (
                len(arguments) >= 2
                and (
                    not isinstance(arguments[1], MLiteral)
                    or not isinstance(arguments[1].value, int)
                    or isinstance(arguments[1].value, bool)
                    or arguments[1].value < 0
                )
            ):
                diagnostics.append(
                    _error(
                        "m.non_negative_row_count_required",
                        "A quantidade de linhas deve ser um inteiro não negativo.",
                        arguments[1],
                    )
                )
        elif name == "Table.SelectRows" and len(arguments) >= 2:
            if not isinstance(arguments[1], MEachExpression):
                diagnostics.append(
                    _error(
                        "m.each_predicate_required",
                        "Table.SelectRows exige um predicado each.",
                        arguments[1],
                    )
                )
        elif name == "Table.AddColumn" and len(arguments) >= 3:
            if not isinstance(arguments[2], MEachExpression):
                diagnostics.append(
                    _error(
                        "m.each_generator_required",
                        "Table.AddColumn exige um gerador each.",
                        arguments[2],
                    )
                )
            if len(arguments) >= 4 and not isinstance(arguments[3], MTypeExpression):
                diagnostics.append(
                    _error(
                        "m.type_expression_required",
                        "O tipo da nova coluna deve usar a sintaxe type.",
                        arguments[3],
                    )
                )
        elif name == "Table.Sort" and len(arguments) >= 2:
            criteria = arguments[1]
            valid = isinstance(criteria, MListExpression) and all(
                isinstance(item, MListExpression)
                and len(item.items) == 2
                and isinstance(item.items[0], MLiteral)
                and isinstance(item.items[0].value, str)
                and isinstance(item.items[1], MIdentifier)
                and item.items[1].name in {"Order.Ascending", "Order.Descending"}
                for item in criteria.items
            )
            if not valid:
                diagnostics.append(
                    _error(
                        "m.invalid_sort_spec",
                        "A ordenação deve ser uma lista de pares {coluna, Order.*}.",
                        criteria,
                    )
                )
        elif name == "Table.ReplaceValue" and len(arguments) >= 5:
            replacer = arguments[3]
            if (
                not isinstance(replacer, MIdentifier)
                or replacer.name not in {"Replacer.ReplaceText", "Replacer.ReplaceValue"}
            ):
                diagnostics.append(
                    _error(
                        "m.replacer_not_allowed",
                        "Use Replacer.ReplaceText ou Replacer.ReplaceValue.",
                        replacer,
                    )
                )
            if _literal_strings(arguments[4]) is None:
                diagnostics.append(
                    _error(
                        "m.literal_column_list_required",
                        "As colunas de substituição devem ser uma lista literal.",
                        arguments[4],
                    )
                )
        elif name == "Table.TransformColumnTypes" and len(arguments) >= 2:
            transformations = arguments[1]
            valid = isinstance(transformations, MListExpression) and all(
                isinstance(item, MListExpression)
                and len(item.items) == 2
                and isinstance(item.items[0], MLiteral)
                and isinstance(item.items[0].value, str)
                and isinstance(item.items[1], MTypeExpression)
                for item in transformations.items
            )
            if not valid:
                diagnostics.append(
                    _error(
                        "m.invalid_type_transform_spec",
                        "A alteração de tipos deve conter pares {coluna, type tipo}.",
                        transformations,
                    )
                )
            if (
                len(arguments) >= 3
                and (
                    not isinstance(arguments[2], MLiteral)
                    or not isinstance(arguments[2].value, str)
                )
            ):
                diagnostics.append(
                    _error(
                        "m.literal_culture_required",
                        "A cultura deve ser texto literal.",
                        arguments[2],
                    )
                )
        elif name == "Table.PromoteHeaders" and len(arguments) >= 2:
            options = arguments[1]
            if isinstance(options, MRecordExpression):
                for field in options.fields:
                    if field.name == "PromoteAllScalars" and (
                        not isinstance(field.value, MLiteral)
                        or not isinstance(field.value.value, bool)
                    ):
                        diagnostics.append(
                            _error(
                                "m.logical_option_required",
                                "PromoteAllScalars deve ser true ou false.",
                                field.value,
                            )
                        )
        elif name == "Table.Group" and len(arguments) >= 3:
            if _literal_strings(arguments[1]) is None or not isinstance(
                arguments[2], MListExpression
            ):
                diagnostics.append(
                    _error(
                        "m.invalid_group_spec",
                        "Table.Group exige chaves literais e agregações em lista.",
                        expression,
                    )
                )
        elif name in {"Table.Unpivot", "Table.UnpivotOtherColumns"} and len(arguments) >= 4:
            if (
                _literal_strings(arguments[1]) is None
                or not isinstance(arguments[2], MLiteral)
                or not isinstance(arguments[2].value, str)
                or not isinstance(arguments[3], MLiteral)
                or not isinstance(arguments[3].value, str)
            ):
                diagnostics.append(
                    _error(
                        "m.invalid_unpivot_spec",
                        "Unpivot exige colunas e nomes de saída literais.",
                        expression,
                    )
                )
        elif name == "Table.NestedJoin" and len(arguments) >= 5:
            valid = (
                _literal_strings(arguments[1]) is not None
                and isinstance(arguments[2], MIdentifier)
                and _literal_strings(arguments[3]) is not None
                and isinstance(arguments[4], MLiteral)
                and isinstance(arguments[4].value, str)
                and (
                    len(arguments) < 6
                    or (
                        isinstance(arguments[5], MIdentifier)
                        and arguments[5].name == "JoinKind.LeftOuter"
                    )
                )
            )
            if not valid:
                diagnostics.append(
                    _error(
                        "m.invalid_nested_join_spec",
                        "NestedJoin aceita somente chaves literais e JoinKind.LeftOuter.",
                        expression,
                    )
                )
        elif name == "Table.ExpandTableColumn" and len(arguments) >= 3:
            valid = (
                isinstance(arguments[1], MLiteral)
                and isinstance(arguments[1].value, str)
                and _literal_strings(arguments[2]) is not None
                and (len(arguments) < 4 or _literal_strings(arguments[3]) is not None)
            )
            if not valid:
                diagnostics.append(
                    _error(
                        "m.invalid_expand_spec",
                        "ExpandTableColumn exige coluna e listas de nomes literais.",
                        expression,
                    )
                )

    def _infer_columns(
        self,
        expression: MCallExpression,
        input_columns: set[str] | None,
        diagnostics: list[Diagnostic],
    ) -> set[str] | None:
        if input_columns is None:
            return None
        columns = set(input_columns)
        name = expression.function_name
        if name == "Table.RenameColumns" and len(expression.arguments) >= 2:
            pairs = _rename_pairs(expression.arguments[1])
            if pairs is None:
                diagnostics.append(
                    _error(
                        "m.invalid_rename_spec",
                        "Renames deve ser uma lista de pares de textos.",
                        expression.arguments[1],
                    )
                )
            else:
                for source, target in pairs:
                    if source not in columns:
                        diagnostics.append(
                            _error(
                                "m.unknown_column",
                                f'A coluna "{source}" não existe no schema informado.',
                                expression.arguments[1],
                            )
                        )
                    columns.discard(source)
                    columns.add(target)
        elif name in {"Table.SelectColumns", "Table.RemoveColumns", "Table.FillDown"} and len(expression.arguments) >= 2:
            selected = _literal_strings(expression.arguments[1])
            if selected is None:
                diagnostics.append(
                    _error(
                        "m.literal_column_list_required",
                        "É necessária uma lista literal de nomes de coluna.",
                        expression.arguments[1],
                    )
                )
            else:
                for column in selected:
                    if column not in columns:
                        diagnostics.append(
                            _error(
                                "m.unknown_column",
                                f'A coluna "{column}" não existe no schema informado.',
                                expression.arguments[1],
                            )
                        )
                if name == "Table.SelectColumns":
                    columns = set(selected)
                elif name == "Table.RemoveColumns":
                    columns.difference_update(selected)
        elif name == "Table.AddColumn" and len(expression.arguments) >= 2:
            column = expression.arguments[1]
            if not isinstance(column, MLiteral) or not isinstance(column.value, str):
                diagnostics.append(
                    _error(
                        "m.literal_column_name_required",
                        "O nome da nova coluna deve ser texto literal.",
                        column,
                    )
                )
            else:
                columns.add(column.value)
        elif name == "Table.Sort" and len(expression.arguments) >= 2:
            criteria = expression.arguments[1]
            if isinstance(criteria, MListExpression):
                for item in criteria.items:
                    if (
                        isinstance(item, MListExpression)
                        and item.items
                        and isinstance(item.items[0], MLiteral)
                        and isinstance(item.items[0].value, str)
                        and item.items[0].value not in columns
                    ):
                        diagnostics.append(
                            _error(
                                "m.unknown_column",
                                f'A coluna "{item.items[0].value}" não existe no schema informado.',
                                item.items[0],
                            )
                        )
        elif name == "Table.ReplaceValue" and len(expression.arguments) >= 5:
            selected = _literal_strings(expression.arguments[4]) or ()
            for column in selected:
                if column not in columns:
                    diagnostics.append(
                        _error(
                            "m.unknown_column",
                            f'A coluna "{column}" não existe no schema informado.',
                            expression.arguments[4],
                        )
                    )
        elif name == "Table.TransformColumnTypes" and len(expression.arguments) >= 2:
            transformations = expression.arguments[1]
            if isinstance(transformations, MListExpression):
                for item in transformations.items:
                    if (
                        isinstance(item, MListExpression)
                        and item.items
                        and isinstance(item.items[0], MLiteral)
                        and isinstance(item.items[0].value, str)
                        and item.items[0].value not in columns
                    ):
                        diagnostics.append(
                            _error(
                                "m.unknown_column",
                                f'A coluna "{item.items[0].value}" não existe no schema informado.',
                                item.items[0],
                            )
                        )
        elif name == "Table.PromoteHeaders":
            return None
        elif name in {
            "Table.Group",
            "Table.Pivot",
            "Table.Unpivot",
            "Table.UnpivotOtherColumns",
            "Table.NestedJoin",
            "Table.ExpandTableColumn",
        }:
            return None
        return columns
