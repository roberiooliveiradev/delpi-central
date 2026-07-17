from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
)
from tv_app.application.services.data.m_query.m_compiler import MCompileRequest, MQueryCompiler
from tv_app.application.services.data.m_query.m_query_dependency_service import (
    MQueryDependencyService,
)
from tv_app.application.services.data.tv_data_transform_service import execute_transform_plan
from tv_app.application.services.data.tv_data_transform_service import (
    apply_data_transform_to_payload_result,
)
from tv_app.main import app


def _compile(script: str, *, bindings=(), target=None, source_schema=()):
    result = MQueryCompiler().compile(
        MCompileRequest(
            profile="m-delpi-v1",
            script=script,
            source_schema=tuple(source_schema),
            query_bindings=tuple(bindings),
            target_step_name=target,
            culture="pt-BR",
        )
    )
    assert result.valid, [item.to_dict() for item in result.diagnostics]
    assert result.plan is not None
    return result


def test_lazy_if_and_short_circuit_do_not_evaluate_failing_branch():
    compiled = _compile(
        """let
    A = Table.AddColumn(Fonte, "ifLazy", each if [ativo] then 10 / [divisor] else 0, type number),
    B = Table.AddColumn(A, "andLazy", each [ativo] and (10 / [divisor] > 1), type logical),
    C = Table.AddColumn(B, "orLazy", each (not [ativo]) or (10 / [divisor] > 1), type logical)
in
    C"""
    )
    result = execute_transform_plan(
        {"columns": ["ativo", "divisor"], "rows": [{"ativo": False, "divisor": 0}]},
        compiled.plan,
    )
    assert result.table["rows"] == [
        {
            "ativo": False,
            "divisor": 0,
            "ifLazy": 0.0,
            "andLazy": False,
            "orLazy": True,
        }
    ]
    assert result.runtime_errors == ()


def test_pt_br_types_schema_and_cell_error_are_structured_not_null():
    compiled = _compile(
        """let
    A = Table.TransformColumnTypes(Fonte, {{"valor", type number}, {"data", type date}}, "pt-BR"),
    B = Table.AddColumn(A, "quociente", each 10 / [divisor], type number)
in
    B"""
    )
    result = execute_transform_plan(
        {
            "columns": ["valor", "data", "divisor"],
            "rows": [{"valor": "1.234,50", "data": "17/07/2026", "divisor": 0}],
        },
        compiled.plan,
    )
    row = result.table["rows"][0]
    assert row["valor"] == 1234.5
    assert row["data"].isoformat() == "2026-07-17"
    assert row["quociente"]["error"]["code"] == "m.division_by_zero"
    assert result.runtime_errors_dict()["count"] == 1
    schema = {item["key"]: item for item in result.schema}
    assert schema["valor"]["typeSource"] == "declared"
    assert schema["data"]["type"] == "date"


def test_group_pivot_and_unpivot_execute_in_canonical_facade():
    grouped = _compile(
        """let
    A = Table.Group(Fonte, {"filial"}, {{"total", each List.Sum([valor]), type number}})
in
    A"""
    )
    group_result = execute_transform_plan(
        {
            "columns": ["filial", "valor"],
            "rows": [
                {"filial": "01", "valor": 2},
                {"filial": "01", "valor": 3},
                {"filial": "02", "valor": 4},
            ],
        },
        grouped.plan,
    )
    assert group_result.table["rows"] == [
        {"filial": "01", "total": 5.0},
        {"filial": "02", "total": 4.0},
    ]

    pivoted = _compile(
        """let
    A = Table.Pivot(Fonte, {"01", "02"}, "filial", "valor", List.Sum),
    B = Table.Unpivot(A, {"01", "02"}, "filial", "valor")
in
    B"""
    )
    pivot_result = execute_transform_plan(
        {
            "columns": ["periodo", "filial", "valor"],
            "rows": [
                {"periodo": "jul", "filial": "01", "valor": 2},
                {"periodo": "jul", "filial": "02", "valor": 3},
            ],
        },
        pivoted.plan,
    )
    assert pivot_result.table["rows"] == [
        {"periodo": "jul", "filial": "01", "valor": 2.0},
        {"periodo": "jul", "filial": "02", "valor": 3.0},
    ]


def test_nested_join_expand_preserves_one_to_many_matches():
    bindings = ({"name": "Produtos", "sourceId": "right"},)
    compiled = _compile(
        """let
    A = Table.NestedJoin(Fonte, {"codigo"}, Produtos, {"codigo"}, "Produtos", JoinKind.LeftOuter),
    B = Table.ExpandTableColumn(A, "Produtos", {"nome"}, {"produto"})
in
    B""",
        bindings=bindings,
    )
    result = execute_transform_plan(
        {"columns": ["codigo"], "rows": [{"codigo": "A"}, {"codigo": "B"}]},
        compiled.plan,
        sibling_tables={
            "Produtos": {
                "columns": ["codigo", "nome"],
                "rows": [
                    {"codigo": "A", "nome": "Um"},
                    {"codigo": "A", "nome": "Dois"},
                ],
            }
        },
    )
    assert result.table["rows"] == [
        {"codigo": "A", "produto": "Um"},
        {"codigo": "A", "produto": "Dois"},
        {"codigo": "B", "produto": None},
    ]


def test_dependency_graph_is_order_independent_and_detects_cycle():
    blocks = [
        {
            "id": "b",
            "queryName": "B",
            "type": "data_source",
            "dataTransform": {
                "version": 2,
                "language": "m-delpi-v1",
                "script": "let X = Table.FirstN(A, 1) in X",
            },
        },
        {
            "id": "a",
            "queryName": "A",
            "type": "data_source",
            "dataTransform": {
                "version": 2,
                "language": "m-delpi-v1",
                "script": "let X = Table.FirstN(Fonte, 1) in X",
            },
        },
    ]
    graph = MQueryDependencyService().resolve(blocks)
    assert graph.valid
    assert graph.ordered_source_ids == ("a", "b")

    blocks[1]["dataTransform"]["script"] = "let X = Table.FirstN(B, 1) in X"
    cyclic = MQueryDependencyService().resolve(blocks)
    assert not cyclic.valid
    assert any(item["code"] == "m.query_cycle" for item in cyclic.diagnostics)


def test_dependency_graph_returns_all_compile_diagnostics():
    graph = MQueryDependencyService().resolve(
        [
            {
                "id": "a",
                "queryName": "A",
                "type": "data_source",
                "dataTransform": {
                    "version": 2,
                    "language": "m-delpi-v1",
                    "script": 'let X = Web.Contents("x") in X',
                },
            },
            {
                "id": "b",
                "queryName": "B",
                "type": "data_source",
                "dataTransform": {
                    "version": 2,
                    "language": "m-delpi-v1",
                    "script": "let X = Table.FirstN(Inexistente, 1) in X",
                },
            },
        ]
    )
    codes = {item["code"] for item in graph.diagnostics}
    assert {"m.function_not_allowed", "m.unknown_identifier"} <= codes


def test_v2_public_adapter_uses_same_facade_when_runtime_flag_is_enabled():
    settings = {
        "enabled": True,
        "profile": "m-delpi-v1",
        "defaultCulture": "pt-BR",
        "maxScriptBytes": 65536,
    }

    def setting(key, default=None):
        return settings.get(key, default)

    with patch(
        "tv_app.application.services.data.data_transform_contract.m_query_setting",
        side_effect=setting,
    ):
        result = apply_data_transform_to_payload_result(
            [{"valor": 1}, {"valor": 2}],
            {
                "version": 2,
                "language": "m-delpi-v1",
                "script": "let A = Table.FirstN(Fonte, 1), B = Table.Skip(A, 1) in B",
            },
            target_step_name="A",
        )
    assert result["applied"] is True
    assert result["data"] == [{"valor": 1}]
    assert result["selectedStepName"] == "A"
    assert result["schema"][0]["type"] == "number"


def test_source_schema_remains_pre_transform_after_column_rename():
    script = (
        'let A = Table.RenameColumns(Fonte, {{"periodo", "periodo_teste"}}) '
        "in A"
    )
    settings = {
        "enabled": True,
        "profile": "m-delpi-v1",
        "defaultCulture": "pt-BR",
        "maxScriptBytes": 65536,
    }

    with patch(
        "tv_app.application.services.data.data_transform_contract.m_query_setting",
        side_effect=lambda key, default=None: settings.get(key, default),
    ):
        result = apply_data_transform_to_payload_result(
            [{"periodo": "01/01/26", "value": None}],
            {"version": 2, "language": "m-delpi-v1", "script": script},
        )

    assert [column["key"] for column in result["sourceSchema"]] == [
        "periodo",
        "value",
    ]
    assert [column["key"] for column in result["schema"]] == [
        "periodo_teste",
        "value",
    ]
    compiled_again = _compile(script, source_schema=result["sourceSchema"])
    assert "m.unknown_column" not in {
        item.code for item in compiled_again.diagnostics
    }


def test_execution_limits_reject_abusive_join_expansion_inside_loop():
    compiled = _compile(
        """let
    A = Table.NestedJoin(Fonte, {"codigo"}, Produtos, {"codigo"}, "Produtos", JoinKind.LeftOuter),
    B = Table.ExpandTableColumn(A, "Produtos", {"nome"})
in
    B""",
        bindings=({"name": "Produtos", "sourceId": "right"},),
    )
    defaults = {
        "executionTimeoutMs": 2000,
        "maxExpressionDepth": 40,
        "maxExecutionRows": 100,
        "maxExecutionColumns": 100,
        "maxExecutionCells": 10000,
        "maxJoinInputRows": 100,
        "maxJoinOutputRows": 1,
        "maxPivotColumns": 100,
    }
    with patch(
        "tv_app.application.services.data.tv_data_transform_service.m_query_setting",
        side_effect=lambda key, default=None: defaults.get(key, default),
    ):
        try:
            execute_transform_plan(
                {"columns": ["codigo"], "rows": [{"codigo": "A"}]},
                compiled.plan,
                sibling_tables={
                    "Produtos": {
                        "columns": ["codigo", "nome"],
                        "rows": [
                            {"codigo": "A", "nome": "Um"},
                            {"codigo": "A", "nome": "Dois"},
                        ],
                    }
                },
            )
        except ValueError as exc:
            assert getattr(exc, "code", "") == "m.limit_join_output_rows"
        else:
            raise AssertionError("A expansão abusiva deveria ser rejeitada.")


def test_all_dependencies_are_branch_authorized_before_any_fetch():
    catalog = Mock()
    catalog.is_allowed.return_value = True
    catalog.get_route.return_value = {
        "tvConstraints": {
            "requiresBranchPermission": True,
            "branchParamAliases": ["branch"],
        }
    }
    gateway = Mock()
    service = ComunicadoDataEnrichmentService(catalog=catalog, gateway=gateway)
    blocks = [
        {
            "id": "a",
            "queryName": "A",
            "type": "data_source",
            "dataBinding": {"operationId": "op-a", "params": {"branch": "01"}},
        },
        {
            "id": "b",
            "queryName": "B",
            "type": "data_source",
            "dataBinding": {"operationId": "op-b", "params": {"branch": "02"}},
        },
    ]
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=["tv-dashboard.view.filial-01"],
    )
    try:
        service.enrich_blocks(blocks, cfg={"blocks": blocks}, user=user)
    except ValueError:
        pass
    else:
        raise AssertionError("A consulta irmã sem RBAC deveria ser rejeitada.")
    gateway.fetch_by_operation_id.assert_not_called()


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


def test_preview_http_accepts_target_step_and_keeps_legacy_resolved_contract():
    client = TestClient(app)
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    returned = {
        "id": "source",
        "resolved": {
            "data": [{"a": 1}],
            "query": {"selectedStepName": "A", "diagnostics": [], "executionMs": 1},
            "preview": {
                "columns": [{"key": "a", "type": "number", "nullable": False}],
                "rows": [{"a": 1}],
                "truncated": False,
                "isSample": False,
            },
        },
    }
    with (
        patch("tv_app.interface.http.routes.data_api_routes.resolve_user", return_value=user),
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
            return_value=returned,
        ) as preview,
    ):
        response = client.post(
            "/data/preview-block",
            json={
                "block": {"id": "source"},
                "nativeConfig": {},
                "targetStepName": "A",
                "previewOptions": {"maxRows": 20, "includeColumnProfile": False},
            },
        )
    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["block"]["resolved"]["data"] == [{"a": 1}]
    assert payload["query"]["selectedStepName"] == "A"
    assert payload["preview"]["rows"] == [{"a": 1}]
    assert preview.call_args.kwargs["target_step_name"] == "A"
