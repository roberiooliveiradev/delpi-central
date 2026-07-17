import json
from dataclasses import FrozenInstanceError
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tv_app.application.services.data.m_query.m_compiler import (
    MCompileRequest,
    MQueryCompiler,
)
from tv_app.application.services.data.m_query.m_formatter import format_m_document
from tv_app.application.services.data.m_query.m_function_registry import get_function_registry
from tv_app.application.services.data.m_query.m_parser import get_m_parser, parse_m_script
from tv_app.domain.data_query.m_ast import MCallExpression
from tv_app.main import app

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = Path(__file__).parent / "fixtures" / "m_query" / "phase2_golden.json"
CORPUS = ROOT / "fixtures" / "tv-dashboard" / "m-query" / "corpus.json"


def _compile(script: str, **kwargs):
    return MQueryCompiler().compile(
        MCompileRequest(profile="m-delpi-v1", script=script, **kwargs)
    )


def _codes(result) -> set[str]:
    return {item.code for item in result.diagnostics}


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


def test_parser_is_lalr_contextual_singleton_with_immutable_positioned_ast():
    assert get_m_parser() is get_m_parser()
    assert get_m_parser().options.parser == "lalr"
    document = parse_m_script(
        'let\n    #"São Paulo" = Table.FirstN(Fonte, 10)\nin\n    #"São Paulo"'
    )
    binding = document.expression.bindings[0]
    assert binding.name == "São Paulo"
    assert binding.source_range.start_line == 2
    assert isinstance(binding.expression, MCallExpression)
    assert binding.expression.source_range.start_offset < binding.expression.source_range.end_offset
    with pytest.raises(FrozenInstanceError):
        binding.name = "Outro"


@pytest.mark.parametrize(
    "case",
    json.loads(GOLDEN.read_text(encoding="utf-8"))["cases"],
    ids=lambda item: item["id"],
)
def test_golden_compile_and_formatter_idempotence(case):
    result = _compile(case["script"])
    assert result.valid, [item.to_dict() for item in result.diagnostics]
    assert result.canonical_script == case["canonical"]
    assert [
        step.function_name for step in result.plan.steps  # type: ignore[union-attr]
    ] == case["operations"]
    reparsed = parse_m_script(result.canonical_script or "")
    assert format_m_document(reparsed) == result.canonical_script


def test_all_mvp_table_functions_compile_to_transform_plan():
    script = """let
    A = Table.RenameColumns(Fonte, {{"a", "b"}}),
    B = Table.SelectColumns(A, {"b", "x"}),
    C = Table.RemoveColumns(B, {"x"}),
    D = Table.SelectRows(C, each [b] <> null and ([b] >= 1 or [b] = 0)),
    E = Table.Sort(D, {{"b", Order.Descending}}),
    F = Table.ReplaceValue(E, "x", "y", Replacer.ReplaceText, {"b"}),
    G = Table.FirstN(F, 10),
    H = Table.LastN(G, 9),
    I = Table.Skip(H, 1),
    J = Table.RemoveLastN(I, 1),
    K = Table.TransformColumnTypes(J, {{"b", type number}}, "pt-BR"),
    L = Table.FillDown(K, {"b"}),
    M = Table.PromoteHeaders(L, [PromoteAllScalars = true]),
    N = Table.AddColumn(M, "dobro", each if [b] = null then 0 else Number.Abs([b] * 2), type number)
in
    N"""
    result = _compile(script)
    assert result.valid, [item.to_dict() for item in result.diagnostics]
    assert result.plan is not None
    assert len(result.plan.steps) == 14
    assert result.output_step_name == "N"


def test_source_schema_unknown_column_and_query_binding_are_analyzed():
    result = _compile(
        'let X = Table.SelectRows(#"Outra consulta", each [inexistente] > 0) in X',
        source_schema=({"key": "valor", "type": "number", "nullable": True},),
        query_bindings=({"name": "Outra consulta", "sourceId": "q-1"},),
    )
    assert "m.unknown_column" not in _codes(result)
    assert result.valid
    assert result.referenced_queries == ("Outra consulta",)

    local = _compile(
        "let X = Table.SelectRows(Fonte, each [inexistente] > 0) in X",
        source_schema=({"key": "valor", "type": "number", "nullable": True},),
    )
    assert "m.unknown_column" in _codes(local)


def test_source_schema_and_target_step_contracts_are_validated():
    invalid_schema = _compile(
        "let X = Table.FirstN(Fonte, 1) in X",
        source_schema=(
            {"key": "a", "type": "binary", "nullable": True},
            {"key": "a", "type": "text", "nullable": True},
        ),
    )
    assert {"m.duplicate_source_column", "m.source_schema_type_invalid"} <= _codes(
        invalid_schema
    )

    targeted = _compile(
        "let X = Table.FirstN(Fonte, 1), Y = Table.Skip(X, 1) in Y",
        target_step_name="X",
    )
    assert targeted.valid
    assert targeted.output_step_name == "X"
    assert targeted.plan is not None and len(targeted.plan.steps) == 1
    missing = _compile(
        "let X = Table.FirstN(Fonte, 1) in X",
        target_step_name="Ausente",
    )
    assert "m.unknown_target_step" in _codes(missing)


@pytest.mark.parametrize(
    ("script", "code"),
    [
        ('let X = Web.Contents("https://example.invalid") in X', "m.function_not_allowed"),
        ('let X = File.Contents("/etc/passwd") in X', "m.function_not_allowed"),
        ('let X = Folder.Files("/") in X', "m.function_not_allowed"),
        ('let X = Sql.Database("host", "db") in X', "m.function_not_allowed"),
        ('let X = Value.NativeQuery(Fonte, "select 1") in X', "m.function_not_allowed"),
        ('let X = Expression.Evaluate("1+1") in X', "m.function_not_allowed"),
        ("let X = #shared in X", "m.identifier_not_allowed"),
        ("let X = Table.FirstN(X, 1) in X", "m.recursion_not_allowed"),
        ("let F = (n) => F(n - 1), X = Table.FirstN(Fonte, 1) in X", "m.user_function_not_allowed"),
        ("let X = Unknown.Run(Fonte) in X", "m.function_not_allowed"),
    ],
)
def test_forbidden_io_dynamic_unknown_and_recursion_have_stable_ranged_diagnostics(
    script, code
):
    result = _compile(script)
    diagnostic = next(item for item in result.diagnostics if item.code == code)
    assert diagnostic.source_range is not None
    assert diagnostic.source_range.start_line == 1


def test_records_are_controlled_and_only_promote_headers_options_are_accepted():
    rejected = _compile(
        'let X = Table.AddColumn(Fonte, "r", each [segredo = 1]) in X'
    )
    assert "m.record_not_allowed" in _codes(rejected)
    unknown_option = _compile(
        "let X = Table.PromoteHeaders(Fonte, [Unsafe = true]) in X"
    )
    assert "m.record_field_not_allowed" in _codes(unknown_option)


def test_settings_limits_are_applied_before_semantics():
    settings = {
        "profile": "m-delpi-v1",
        "maxScriptBytes": 20,
        "maxSteps": 1,
        "maxAstNodes": 5000,
        "maxExpressionDepth": 8,
        "diagnosticSampleLimit": 20,
    }

    def setting(key, default=None):
        return settings.get(key, default)

    with patch(
        "tv_app.application.services.data.m_query.m_compiler.m_query_setting",
        side_effect=setting,
    ):
        oversized = _compile("let X = Table.FirstN(Fonte, 1) in X")
    assert _codes(oversized) == {"m.limit_script_bytes"}

    settings["maxScriptBytes"] = 10000
    with patch(
        "tv_app.application.services.data.m_query.m_compiler.m_query_setting",
        side_effect=setting,
    ):
        too_many = _compile(
            "let X = Table.FirstN(Fonte, 1), Y = Table.FirstN(X, 1) in Y"
        )
        too_deep = _compile(
            'let X = Table.AddColumn(Fonte, "x", each ((((((((([a])))))))))) in X'
        )
    assert "m.limit_steps" in _codes(too_many)
    assert "m.limit_expression_depth" in _codes(too_deep)


def test_phase0_invalid_corpus_keeps_expected_security_codes():
    corpus = json.loads(CORPUS.read_text(encoding="utf-8"))
    supported = {
        "syntax-missing-in",
        "duplicate-step",
        "unknown-reference",
        "web-contents",
        "file-contents",
        "sql-database",
        "native-query",
        "expression-evaluate",
        "shared-environment",
        "user-function-recursion",
        "adversarial-deep-expression",
        "adversarial-comment-boundary",
        "adversarial-homoglyph-function",
        "adversarial-oversized-token",
    }
    for case in corpus["invalid"]:
        if case["id"] not in supported:
            continue
        script = case.get("script")
        if script is None:
            generator = case["generator"]
            script = (
                generator["prefix"]
                + generator["token"] * generator["count"]
                + generator["suffix"]
            )
        result = _compile(script)
        assert case["expectedCode"] in _codes(result), case["id"]


def test_registry_is_complete_immutable_and_deny_by_default():
    registry = get_function_registry()
    assert registry.resolve("Table.AddColumn") is not None
    assert registry.resolve("Web.Contents") is None
    item = registry.resolve("Table.AddColumn")
    assert item is not None
    assert item.signature and item.category and item.description and item.examples
    assert item.introduced_in == "1.0.0"
    with pytest.raises(TypeError):
        registry.functions["Web.Contents"] = item


def test_compile_and_functions_http_use_envelope_and_tv_read_rbac():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with patch(
        "tv_app.interface.http.routes.data_api_routes.resolve_user",
        return_value=user,
    ), patch(
        "tv_app.middleware.auth_middleware._base_jwt_middleware",
        side_effect=_bypass_auth_middleware,
    ):
        compiled = client.post(
            "/data/m/compile",
            json={
                "profile": "m-delpi-v1",
                "script": "let X = Table.FirstN(Fonte, 1) in X",
                "sourceSchema": [],
                "queryBindings": [],
                "targetStepName": None,
                "culture": "pt-BR",
            },
        )
        functions = client.get("/data/m/functions?profile=m-delpi-v1")
    assert compiled.status_code == 200
    assert compiled.json()["success"] is True
    assert compiled.json()["data"]["outputStepName"] == "X"
    assert functions.status_code == 200
    assert functions.json()["data"]["total"] >= 14

    with patch(
        "tv_app.interface.http.routes.data_api_routes.resolve_user",
        return_value=None,
    ), patch(
        "tv_app.middleware.auth_middleware._base_jwt_middleware",
        side_effect=_bypass_auth_middleware,
    ):
        forbidden = client.get("/data/m/functions")
    assert forbidden.status_code == 403
    assert forbidden.json()["success"] is False


def test_compile_endpoint_never_calls_preview_or_fetch_services():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with (
        patch(
            "tv_app.interface.http.routes.data_api_routes.resolve_user",
            return_value=user,
        ),
        patch(
            "tv_app.middleware.auth_middleware._base_jwt_middleware",
            side_effect=_bypass_auth_middleware,
        ),
        patch.object(
            __import__(
                "tv_app.interface.http.routes.data_api_routes",
                fromlist=["_preview"],
            )._preview,
            "preview_block",
        ) as preview,
    ):
        response = client.post(
            "/data/m/compile",
            json={"script": "let X = Table.FirstN(Fonte, 1) in X"},
        )
    assert response.status_code == 200
    preview.assert_not_called()
