from tv_app.application.services.data.m_query.m_compiler import MCompileRequest, MQueryCompiler
from tv_app.application.services.data.m_query.m_mutation_service import MQueryMutationService


SCRIPT = (
    "let\n"
    '    #"Linhas iniciais" = Table.Skip(Fonte, 1),\n'
    '    Final = Table.FirstN(#"Linhas iniciais", 10)\n'
    "in\n"
    "    Final"
)


def test_compile_exposes_server_driven_completion_and_syntax_context():
    result = MQueryCompiler().compile(
        MCompileRequest(
            profile="m-delpi-v1",
            script=SCRIPT,
            source_schema=({"key": "valor", "type": "number", "nullable": True},),
            query_bindings=({"name": "Consulta origem", "sourceId": "q1"},),
        )
    )
    payload = result.to_dict()
    assert result.valid
    assert {"Linhas iniciais", "Final"} <= set(payload["completionContext"]["steps"])
    assert payload["completionContext"]["columns"] == ["valor"]
    assert payload["completionContext"]["queries"] == ["Consulta origem"]
    assert {
        (item["kind"], item["insertText"])
        for item in payload["completionContext"]["items"]
    } >= {
        ("column", "[valor]"),
        ("query", '#"Consulta origem"'),
        ("step", '#"Linhas iniciais"'),
    }
    assert any(
        SCRIPT[item["startOffset"] : item["endOffset"]] == "let"
        and item["kind"] == "keyword"
        for item in payload["syntaxTokens"]
    )


def test_formatter_is_idempotent_and_rename_step_updates_references():
    service = MQueryMutationService()
    formatted = service.mutate(
        MCompileRequest(profile="m-delpi-v1", script=SCRIPT),
        {"type": "format_script"},
    )
    formatted_again = service.mutate(
        MCompileRequest(profile="m-delpi-v1", script=formatted.canonical_script or ""),
        {"type": "format_script"},
    )
    assert formatted_again.canonical_script == formatted.canonical_script

    renamed = service.mutate(
        MCompileRequest(profile="m-delpi-v1", script=formatted.canonical_script or ""),
        {
            "type": "rename_step",
            "stepName": "Linhas iniciais",
            "newName": "Amostra",
        },
    )
    assert renamed.valid
    assert "Table.FirstN(Amostra, 10)" in (renamed.canonical_script or "")
    assert "Linhas iniciais" not in (renamed.canonical_script or "")


def test_rename_query_updates_ast_references_without_text_replacement():
    script = "let\n    Mesclada = Table.Combine({Fonte, #\"Consulta origem\"})\nin\n    Mesclada"
    renamed = MQueryMutationService().mutate(
        MCompileRequest(
            profile="m-delpi-v1",
            script=script,
            query_bindings=({"name": "Consulta nova", "sourceId": "q1"},),
        ),
        {
            "type": "rename_query",
            "from": "Consulta origem",
            "to": "Consulta nova",
        },
    )
    assert renamed.valid
    assert '#"Consulta nova"' in (renamed.canonical_script or "")
    assert "Consulta origem" not in (renamed.canonical_script or "")
