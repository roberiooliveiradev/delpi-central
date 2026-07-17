from __future__ import annotations

from datetime import date

from tv_app.application.services.data.m_query.m_compiler import MCompileRequest, MQueryCompiler
from tv_app.application.services.data.m_query.m_function_registry import get_function_registry
from tv_app.application.services.data.m_query.m_mutation_service import MQueryMutationService
from tv_app.application.services.data.tv_data_transform_service import execute_transform_plan


def _compile(script: str, *, bindings=()):
    result = MQueryCompiler().compile(
        MCompileRequest(
            profile="m-delpi-v1",
            script=script,
            query_bindings=tuple(bindings),
            culture="pt-BR",
        )
    )
    assert result.valid, [item.to_dict() for item in result.diagnostics]
    assert result.plan is not None
    return result


def test_phase5_registry_entries_are_complete_and_deny_by_default():
    registry = get_function_registry()
    required = {
        "Table.ReorderColumns",
        "Table.DuplicateColumn",
        "Table.SplitColumn",
        "Table.AddIndexColumn",
        "Table.Distinct",
        "Table.Range",
        "Table.FillUp",
        "Table.Transpose",
        "Table.ReverseRows",
        "Table.Combine",
        "Table.TransformColumns",
        "Table.RemoveRowsWithErrors",
        "Table.ReplaceErrorValues",
        "Splitter.SplitTextByDelimiter",
    }
    assert required <= set(registry.functions)
    for name in required:
        spec = registry.functions[name]
        assert spec.category and spec.signature and spec.examples and spec.parameters


def test_phase5_column_row_text_number_and_index_golden():
    compiled = _compile(
        """let
    A = Table.ReorderColumns(Fonte, {"codigo", "valor"}),
    B = Table.DuplicateColumn(A, "codigo", "codigo copia"),
    C = Table.SplitColumn(B, "codigo copia", Splitter.SplitTextByDelimiter("-", QuoteStyle.Csv), {"familia", "item"}),
    D = Table.AddIndexColumn(C, "Índice", 1, 1, type number),
    E = Table.TransformColumns(D, {{"familia", each Text.Upper(Text.Trim(_)), type text}, {"valor", each Number.Abs(_), type number}}),
    F = Table.Distinct(E, {"codigo"}),
    G = Table.Range(F, 0, 2),
    H = Table.ReverseRows(G)
in
    H"""
    )
    result = execute_transform_plan(
        {
            "columns": ["extra", "valor", "codigo"],
            "rows": [
                {"extra": "x", "valor": -2, "codigo": " a-1"},
                {"extra": "x", "valor": -3, "codigo": "b-2"},
                {"extra": "y", "valor": -4, "codigo": "b-2"},
            ],
        },
        compiled.plan,
    )
    assert result.table["columns"] == [
        "codigo",
        "valor",
        "extra",
        "familia",
        "item",
        "Índice",
    ]
    assert result.table["rows"][0]["familia"] == "B"
    assert result.table["rows"][1]["valor"] == 2.0


def test_phase5_append_fill_transpose_and_explicit_error_treatment():
    append = _compile(
        """let
    A = Table.Combine({Fonte, Anterior}),
    B = Table.FillUp(A, {"grupo"})
in
    B""",
        bindings=({"name": "Anterior", "sourceId": "old"},),
    )
    result = execute_transform_plan(
        {"columns": ["grupo", "valor"], "rows": [{"grupo": None, "valor": 1}]},
        append.plan,
        sibling_tables={
            "Anterior": {
                "columns": ["grupo", "valor", "extra"],
                "rows": [{"grupo": "G", "valor": 2, "extra": True}],
            }
        },
    )
    assert result.table["columns"] == ["grupo", "valor", "extra"]
    assert result.table["rows"][0]["grupo"] == "G"

    errors = _compile(
        """let
    A = Table.TransformColumnTypes(Fonte, {{"valor", type number}}, "pt-BR"),
    B = Table.ReplaceErrorValues(A, {{"valor", 0}})
in
    B"""
    )
    treated = execute_transform_plan(
        {"columns": ["valor"], "rows": [{"valor": "inválido"}]},
        errors.plan,
    )
    assert treated.table["rows"] == [{"valor": 0}]
    assert treated.runtime_errors[0].code == "m.number_conversion"

    transposed = _compile("let A = Table.Transpose(Fonte) in A")
    transpose_result = execute_transform_plan(
        {"columns": ["a", "b"], "rows": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]},
        transposed.plan,
    )
    assert transpose_result.table == {
        "columns": ["Column1", "Column2"],
        "rows": [
            {"Column1": 1, "Column2": 3},
            {"Column1": 2, "Column2": 4},
        ],
    }


def test_every_phase5_ribbon_operation_is_mutated_and_compiled_server_side():
    service = MQueryMutationService()
    request = MCompileRequest(
        profile="m-delpi-v1",
        script="let A = Table.FirstN(Fonte, 10) in A",
        query_bindings=({"name": "Outra", "sourceId": "other"},),
    )
    actions = [
        ("remove_columns", {"columns": ["codigo"]}),
        ("reorder_columns", {"columns": ["codigo"]}),
        ("changeType", {"column": "codigo", "to": "date"}),
        ("duplicate_column", {"column": "codigo", "newName": "copia"}),
        ("split_column", {"column": "codigo", "delimiter": "-", "newColumns": ["a", "b"]}),
        ("add_index", {"newName": "Índice", "initial": 1, "increment": 1}),
        ("distinct_rows", {"columns": ["codigo"]}),
        ("range_rows", {"offset": 1, "count": 2}),
        ("fill_up", {"column": "codigo"}),
        ("transpose", {}),
        ("reverse_rows", {}),
        ("append_queries", {"queries": ["Outra"]}),
        ("transform_column", {"column": "codigo", "function": "trim", "arguments": []}),
        ("remove_errors", {"columns": ["codigo"]}),
        ("replace_errors", {"column": "codigo", "replacement": 0}),
        (
            "add_custom_column",
            {"newName": "copia", "expression": "[codigo]", "type": "text"},
        ),
        (
            "add_conditional_column",
            {
                "column": "valor",
                "newName": "faixa",
                "operator": "gte",
                "value": 10,
                "thenValue": "alta",
                "elseValue": "baixa",
            },
        ),
        (
            "group_rows",
            {
                "keys": ["codigo"],
                "valueColumn": "valor",
                "aggregate": "sum",
                "output": "total",
            },
        ),
        (
            "pivot",
            {
                "values": ["A"],
                "attributeColumn": "codigo",
                "valueColumn": "valor",
            },
        ),
        (
            "unpivot",
            {
                "columns": ["valor"],
                "attributeName": "atributo",
                "valueName": "valor",
            },
        ),
        (
            "nested_join",
            {
                "query": "Outra",
                "leftKeys": ["codigo"],
                "rightKeys": ["codigo"],
                "newColumn": "Outra",
            },
        ),
        (
            "expand_table_column",
            {
                "column": "Outra",
                "columns": ["valor"],
                "newColumnNames": ["valor outra"],
            },
        ),
    ]
    for operation, arguments in actions:
        result = service.mutate(
            request,
            {
                "type": "insert_step",
                "afterStepName": "A",
                "stepName": operation,
                "operation": operation,
                "arguments": arguments,
            },
        )
        assert result.valid, (operation, [item.to_dict() for item in result.diagnostics])
        assert result.canonical_script


def test_phase5_optional_duplicate_type_and_full_type_mutation_execute():
    service = MQueryMutationService()
    request = MCompileRequest(
        profile="m-delpi-v1",
        script="let A = Table.FirstN(Fonte, 10) in A",
    )
    typed = service.mutate(
        request,
        {
            "type": "insert_step",
            "afterStepName": "A",
            "stepName": "Data tipada",
            "operation": "changeType",
            "arguments": {"column": "data", "to": "date"},
        },
    )
    assert typed.valid
    duplicated = _compile(
        'let A = Table.DuplicateColumn(Fonte, "data", "data copia", type date) in A'
    )
    result = execute_transform_plan(
        {"columns": ["data"], "rows": [{"data": "17/07/2026"}]},
        duplicated.plan,
    )
    assert result.table["rows"] == [
        {"data": "17/07/2026", "data copia": date(2026, 7, 17)}
    ]


def test_phase5_mutation_quotes_reserved_query_names():
    result = MQueryMutationService().mutate(
        MCompileRequest(
            profile="m-delpi-v1",
            script="let A = Table.FirstN(Fonte, 10) in A",
            query_bindings=({"name": "let", "sourceId": "reserved"},),
        ),
        {
            "type": "insert_step",
            "afterStepName": "A",
            "stepName": "Consultas acrescentadas",
            "operation": "append_queries",
            "arguments": {"queries": ["let"]},
        },
    )

    assert result.valid
    assert '#"let"' in result.canonical_script


def test_phase5_splitter_and_index_shapes_are_rejected_semantically():
    invalid_scripts = (
        'let A = Table.SplitColumn(Fonte, "codigo", '
        'Splitter.SplitTextByDelimiter("-", 1), {"a", "b"}) in A',
        'let A = Table.AddIndexColumn(Fonte, "Índice", "um", 1) in A',
        'let A = Table.NestedJoin(Fonte, {"codigo"}, Intrusa, {"codigo"}, '
        '"Intrusa", JoinKind.LeftOuter) in A',
    )
    for script in invalid_scripts:
        result = MQueryCompiler().compile(
            MCompileRequest(profile="m-delpi-v1", script=script)
        )
        assert not result.valid
        assert result.diagnostics
