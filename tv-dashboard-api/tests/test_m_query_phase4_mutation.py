from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient

from tv_app.application.services.data.m_query.m_compiler import MCompileRequest, MQueryCompiler
from tv_app.application.services.data.m_query.m_mutation_service import MQueryMutationService
from tv_app.main import app


async def _bypass_auth_middleware(request, call_next):
    return await call_next(request)


def _request(script: str) -> MCompileRequest:
    return MCompileRequest(profile="m-delpi-v1", script=script)


def test_mutations_are_canonical_and_address_steps_by_name():
    service = MQueryMutationService()
    inserted = service.mutate(
        _request("let\n    Inicial = Table.FirstN(Fonte, 10)\nin\n    Inicial"),
        {
            "type": "insert_step",
            "afterStepName": "Inicial",
            "stepName": "Ordenado",
            "operation": "sort",
            "arguments": {"column": "valor", "direction": "desc"},
        },
    )
    assert inserted.valid
    assert inserted.output_step_name == "Ordenado"
    assert 'Table.Sort(Inicial, {{"valor", Order.Descending}})' in (
        inserted.canonical_script or ""
    )

    renamed = service.mutate(
        _request(inserted.canonical_script or ""),
        {"type": "rename_step", "stepName": "Inicial", "newName": "Amostra"},
    )
    assert renamed.valid
    assert "Table.Sort(Amostra" in (renamed.canonical_script or "")

    removed = service.mutate(
        _request(renamed.canonical_script or ""),
        {"type": "remove_step", "stepName": "Ordenado"},
    )
    assert removed.valid
    assert removed.output_step_name == "Amostra"


def test_insert_sort_replaces_adjacent_sort_instead_of_stacking():
    service = MQueryMutationService()
    script = (
        "let\n"
        "    Inicial = Table.FirstN(Fonte, 10),\n"
        '    Ordenado = Table.Sort(Inicial, {{"valor", Order.Ascending}})\n'
        "in\n"
        "    Ordenado"
    )

    # Etapa selecionada é a anterior ao sort: reordenar deve atualizar o sort
    # adjacente (comportamento Power Query), não empilhar um novo.
    updated = service.mutate(
        _request(script),
        {
            "type": "insert_step",
            "afterStepName": "Inicial",
            "stepName": "Linhas ordenadas",
            "operation": "sort",
            "arguments": {"column": "valor", "direction": "desc"},
        },
    )
    assert updated.valid
    canonical = updated.canonical_script or ""
    assert canonical.count("Table.Sort") == 1
    assert 'Table.Sort(Inicial, {{"valor", Order.Descending}})' in canonical
    assert updated.output_step_name == "Ordenado"

    # Etapa selecionada é o próprio sort: alternar direção substitui os critérios.
    toggled = service.mutate(
        _request(canonical),
        {
            "type": "insert_step",
            "afterStepName": "Ordenado",
            "stepName": "Linhas ordenadas",
            "operation": "sort",
            "arguments": {"column": "valor", "direction": "asc"},
        },
    )
    assert toggled.valid
    toggled_canonical = toggled.canonical_script or ""
    assert toggled_canonical.count("Table.Sort") == 1
    assert 'Table.Sort(Inicial, {{"valor", Order.Ascending}})' in toggled_canonical


def test_insert_sort_after_non_sort_step_still_inserts():
    service = MQueryMutationService()
    result = service.mutate(
        _request("let\n    Inicial = Table.FirstN(Fonte, 10)\nin\n    Inicial"),
        {
            "type": "insert_step",
            "afterStepName": "Inicial",
            "stepName": "Linhas ordenadas",
            "operation": "sort",
            "arguments": {"column": "valor", "direction": "asc"},
        },
    )
    assert result.valid
    assert (result.canonical_script or "").count("Table.Sort") == 1
    assert result.output_step_name == "Linhas ordenadas"


def test_replace_expression_and_format_are_server_driven():
    service = MQueryMutationService()
    replaced = service.mutate(
        _request("let X = Table.FirstN(Fonte, 1) in X"),
        {
            "type": "replace_step_expression",
            "stepName": "X",
            "expression": "Table.Skip(Fonte, 2)",
        },
    )
    assert replaced.valid
    assert replaced.to_dict()["steps"][0]["formula"] == "Table.Skip(Fonte, 2)"
    formatted = service.mutate(
        _request(replaced.canonical_script or ""),
        {"type": "format_script"},
    )
    assert formatted.canonical_script == replaced.canonical_script


def test_fonte_is_a_named_preview_target_without_persisted_index():
    result = MQueryCompiler().compile(
        MCompileRequest(
            profile="m-delpi-v1",
            script="let X = Table.FirstN(Fonte, 1) in X",
            target_step_name="Fonte",
        )
    )
    assert result.valid
    assert result.output_step_name == "Fonte"
    assert result.plan is not None and result.plan.steps == ()


def test_mutate_and_capabilities_http_contracts():
    user = SimpleNamespace(is_superadmin=True, permissions=[])
    client = TestClient(app)
    with patch(
        "tv_app.interface.http.routes.data_api_routes.resolve_user",
        return_value=user,
    ), patch(
        "tv_app.middleware.auth_middleware._base_jwt_middleware",
        side_effect=_bypass_auth_middleware,
    ):
        response = client.post(
            "/data/m/mutate",
            json={
                "script": "let X = Table.FirstN(Fonte, 1) in X",
                "action": {
                    "type": "insert_step",
                    "afterStepName": "X",
                    "stepName": "Y",
                    "operation": "removeRows",
                    "arguments": {"count": 1, "from": "top"},
                },
            },
        )
        capabilities = client.get("/data/m/capabilities")
    assert response.status_code == 200
    assert response.json()["data"]["outputStepName"] == "Y"
    assert capabilities.status_code == 200
    assert capabilities.json()["data"]["enabled"] is True
    assert capabilities.json()["data"]["writeV2Enabled"] is True
    assert capabilities.json()["data"]["advancedEditorEnabled"] is True
