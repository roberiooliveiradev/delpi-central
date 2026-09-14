"""Tests for Custom GPT Actions facade (contract + dispatch wiring)."""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.entities import (
    GptEntity,
    entity_supports,
    parse_entity,
)
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID,
    _ENTITY_DESCRIPTION,
    build_gpt_actions_openapi,
    count_operations,
    resolve_gpt_actions_server_url,
)
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)

# Literal operationIds for audit_route_test_coverage.py (substring scan).
_COVERAGE_ANCHORS = (
    "gpt_get_catalog",
    "gpt_analyze",
    "gpt_search_records",
    "gpt_get_record",
    "gpt_create_record",
    "gpt_update_record",
    "gpt_delete_record",
    "gpt_duplicate_record",
    "gpt_activate_revision",
    "gpt_recalculate_dashboard",
    "gpt_meeting_minute_workflow",
    "gpt_commit_improvement_package",
    "gpt_validate_improvement_package",
    "gpt_get_process_context",
    "gpt_get_openapi_schema",
)


def test_coverage_anchors_match_builder():
    assert set(GPT_ACTIONS_OPERATION_IDS) <= set(_COVERAGE_ANCHORS)
    assert GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID in _COVERAGE_ANCHORS
    assert GPT_ACTIONS_SCHEMA_HTTP_OPERATION_ID not in GPT_ACTIONS_OPERATION_IDS


def test_openapi_has_at_most_30_operations():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) <= 30
    assert count_operations(doc) == len(GPT_ACTIONS_OPERATION_IDS)


def test_openapi_operation_ids_unique_and_stable():
    doc = build_gpt_actions_openapi()
    found: list[str] = []
    for methods in doc["paths"].values():
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            found.append(op["operationId"])
    assert sorted(found) == sorted(GPT_ACTIONS_OPERATION_IDS)
    assert len(found) == len(set(found))


def test_openapi_paths_are_english_only():
    doc = build_gpt_actions_openapi()
    for path in doc["paths"]:
        assert path.startswith("/transformometro/gpt-actions/v1/")
        assert "processos" not in path
        assert "revisoes" not in path
        assert "filiais" not in path


def test_openapi_servers_url_is_absolute_https():
    """OpenAI Custom GPT rejects relative servers[].url."""
    assert resolve_gpt_actions_server_url(
        public_base_url="https://minhadelpi.com.br",
        root_path="/apps/transformometro-api",
    ) == "https://minhadelpi.com.br/apps/transformometro-api"
    doc = build_gpt_actions_openapi(
        server_url="https://minhadelpi.com.br/apps/transformometro-api"
    )
    url = doc["servers"][0]["url"]
    assert url.startswith("https://")
    assert url.endswith("/apps/transformometro-api")
    # relative leftover must not be used as the live default
    fallback = build_gpt_actions_openapi()
    assert fallback["servers"][0]["url"].startswith("http")


def test_openapi_respects_openai_custom_gpt_description_limits():
    """GPT Builder: param description ≤700, operation description ≤300."""
    doc = build_gpt_actions_openapi()
    assert len(_ENTITY_DESCRIPTION) <= 700
    create_desc = doc["paths"][
        "/transformometro/gpt-actions/v1/records/{entity}"
    ]["post"]["description"]
    assert len(create_desc) <= 300
    for methods in doc["paths"].values():
        for method, op in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete"}:
                continue
            desc = op.get("description") or ""
            assert len(desc) <= 300, op.get("operationId")
            for param in op.get("parameters") or []:
                pdesc = param.get("description") or ""
                assert len(pdesc) <= 700, param.get("name")
    assert "/transformometro/gpt-actions/v1/openapi.json" not in doc["paths"]


def test_parse_entity_rejects_unknown():
    with pytest.raises(ValueError, match="Unknown entity"):
        parse_entity("unknown_thing")
    assert parse_entity("process") is GptEntity.PROCESS


def test_entity_capabilities_negative():
    assert entity_supports(GptEntity.PROCESS, "create")
    assert not entity_supports(GptEntity.MEASUREMENT, "delete")
    assert not entity_supports(GptEntity.IMPACT_EFFORT_MATRIX, "create")


def test_dispatch_create_process_positive(tm_client):
    """Sibling of CRUD create_processo via GPT facade."""
    fake_row = {
        "processo_id": "11111111-1111-1111-1111-111111111111",
        "nome_processo": "GPT Processo",
        "status_processo": "ativo",
    }
    with (
        patch(
            "tm_app.application.services.process_write_service.ProcessoRepository"
        ) as repo_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.AuditRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.notify_from_audit"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.DashboardRecalcHookService"
        ),
    ):
        repo = repo_cls.return_value
        repo.create.return_value = fake_row
        repo.get.return_value = fake_row
        response = tm_client.post(
            "/transformometro/gpt-actions/v1/records/process",
            json={
                "data": {
                    "nome_processo": "GPT Processo",
                    "status_processo": "ativo",
                }
            },
        )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["data"]["nome_processo"] == "GPT Processo"


def test_dispatch_create_instance_sibling(tm_client):
    processo_id = "22222222-2222-2222-2222-222222222222"
    instancia = {
        "instancia_id": "33333333-3333-3333-3333-333333333333",
        "processo_id": processo_id,
        "filial_id": "01",
        "status_instancia": "ativo",
    }
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
        ) as proc_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoInstanciaRepository"
        ) as inst_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.assert_filial_ativa"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.AuditRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.notify_from_audit"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_manage_filial_access",
            return_value=None,
        ),
    ):
        proc_cls.return_value.get.return_value = {"processo_id": processo_id}
        inst_cls.return_value.create.return_value = instancia
        response = tm_client.post(
            "/transformometro/gpt-actions/v1/records/instance",
            json={
                "data": {
                    "processo_id": processo_id,
                    "filial_id": "01",
                    "setor_ids": ["engenharia"],
                    "status_instancia": "ativo",
                }
            },
        )
    assert response.status_code == 201
    assert response.json()["data"]["instancia_id"] == instancia["instancia_id"]


def test_dispatch_unknown_entity_negative(tm_client):
    response = tm_client.get("/transformometro/gpt-actions/v1/records/not_an_entity")
    assert response.status_code == 400
    assert response.json()["success"] is False


def test_dispatch_analyze_meta(tm_client):
    with patch(
        "tm_app.interface.http.routes.gpt_actions_routes._dispatch.analyze",
        return_value={"mode": "live", "row_count": 0},
    ):
        response = tm_client.get(
            "/transformometro/gpt-actions/v1/analysis",
            params={"view": "meta"},
        )
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["data"]["mode"] == "live"


def test_gpt_openapi_schema_endpoint_public(tm_client):
    response = tm_client.get("/transformometro/gpt-actions/v1/openapi.json")
    assert response.status_code == 200
    payload = response.json()
    # Envelope is NOT used — raw OpenAPI document
    assert payload.get("openapi") in {"3.1.0", "3.1.1"}
    assert "gpt_analyze" in str(payload)
    assert "/transformometro/gpt-actions/v1/openapi.json" not in (payload.get("paths") or {})


def test_openapi_version_is_31_for_custom_gpt_builder():
    doc = build_gpt_actions_openapi()
    assert doc["openapi"] in {"3.1.0", "3.1.1"}


def test_gpt_create_without_capability(tm_client):
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/records/impact_effort_matrix",
        json={"data": {"modo": "auto"}},
    )
    assert response.status_code == 400
    assert "does not support" in response.json()["message"]


def test_auth_middleware_marks_gpt_openapi_public():
    from tm_app.middleware.auth_middleware import PUBLIC_EXACT, _is_public

    assert "/transformometro/gpt-actions/v1/openapi.json" in PUBLIC_EXACT
    assert _is_public("/transformometro/gpt-actions/v1/openapi.json")
    assert not _is_public("/transformometro/gpt-actions/v1/catalog")


def test_real_jwt_middleware_rejects_write_without_bearer():
    """Negative: protected GPT write without Authorization → 401."""
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from tm_app.interface.http.routes.gpt_actions_routes import router as gpt_router
    from tm_app.middleware.auth_middleware import jwt_middleware

    app = FastAPI()
    app.middleware("http")(jwt_middleware)
    app.include_router(gpt_router)
    client = TestClient(app)

    openapi = client.get("/transformometro/gpt-actions/v1/openapi.json")
    assert openapi.status_code == 200

    denied = client.post(
        "/transformometro/gpt-actions/v1/records/process",
        json={"data": {"nome_processo": "x", "status_processo": "ativo"}},
    )
    assert denied.status_code == 401


def test_dispatch_service_rejects_unsupported_delete():
    service = GptActionsDispatchService()
    request = MagicMock()
    with pytest.raises(GptActionsError, match="does not support"):
        service.delete_record(request, "measurement", "x")


def _gpt_client_without_universal_mocks():
    """Client sem universal_route_mocks — necessário para testes de RBAC reais."""
    from starlette.testclient import TestClient

    from tests.support.test_app import create_test_app

    return TestClient(create_test_app())


def test_gpt_catalog_forbidden_without_view():
    """Negative: authenticated user without transformometro.view → 403."""
    from tests.support import test_app as support

    client = _gpt_client_without_universal_mocks()
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = []
    try:
        response = client.get("/transformometro/gpt-actions/v1/catalog")
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert "transformometro.view" in response.json()["message"]


def test_gpt_analyze_forbidden_without_view():
    from tests.support import test_app as support

    client = _gpt_client_without_universal_mocks()
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = ["commercial.access"]
    try:
        with patch(
            "tm_app.application.gpt_actions.dispatch_service.DashboardSnapshotReadService"
        ):
            response = client.get(
                "/transformometro/gpt-actions/v1/analysis",
                params={"view": "summary", "filial_id": "01"},
            )
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
    assert response.status_code == 403


def test_gpt_catalog_allowed_with_legacy_view():
    from tests.support import test_app as support

    client = _gpt_client_without_universal_mocks()
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = ["transformometro.view"]
    try:
        with (
            patch(
                "tm_app.application.gpt_actions.dispatch_service.FilialRepository"
            ) as filial_cls,
            patch(
                "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
            ) as setor_cls,
            patch(
                "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
            ) as proc_cls,
        ):
            filial_cls.return_value.list_for_options.return_value = []
            setor_cls.return_value.list_for_options.return_value = []
            proc_cls.return_value.list_distinct_tag_values.return_value = []
            response = client.get("/transformometro/gpt-actions/v1/catalog")
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_gpt_delete_measurement_capability_denied(tm_client):
    """Negative sibling: measurement delete is not a GPT capability."""
    response = tm_client.delete(
        "/transformometro/gpt-actions/v1/records/measurement/m1"
    )
    assert response.status_code == 400
    assert "does not support" in response.json()["message"]


def test_gpt_meeting_minute_cancel_without_manage_forbidden():
    from tests.support import test_app as support

    client = _gpt_client_without_universal_mocks()
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = ["transformometro.view"]
    try:
        with patch(
            "tm_app.application.gpt_actions.dispatch_service.MeetingMinutesService"
        ) as svc_cls:
            instance = MagicMock()
            instance.cancel.side_effect = PermissionError(
                "Sem permissão para gerenciar atas."
            )
            svc_cls.return_value = instance
            # Rebind dispatcher singleton's minutes service
            from tm_app.interface.http.routes import gpt_actions_routes as routes

            routes._dispatch._minutes = instance
            response = client.post(
                "/transformometro/gpt-actions/v1/meeting-minutes/mm1/workflow",
                json={"action": "cancel", "reason": "teste"},
            )
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
    assert response.status_code == 403


def test_gpt_create_measurement_sibling(tm_client):
    """Sibling: upsert measurement via GPT facade."""
    medicao = {
        "medicao_id": "44444444-4444-4444-4444-444444444444",
        "revisao_id": "55555555-5555-5555-5555-555555555555",
        "competencia": "2026-09",
        "volume_mensal": 10,
    }
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.MedicaoRepository"
        ) as repo_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.AuditRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.notify_from_audit"
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.DashboardRecalcHookService"
        ),
    ):
        repo_cls.return_value.upsert.return_value = medicao
        response = tm_client.post(
            "/transformometro/gpt-actions/v1/records/measurement",
            json={
                "data": {
                    "revisao_id": medicao["revisao_id"],
                    "volume_mensal": 10,
                    "tempo_medio_execucao_min": 5,
                }
            },
        )
    assert response.status_code == 200
    assert response.json()["data"]["medicao_id"] == medicao["medicao_id"]


def test_registration_guide_exposes_entity_schemas():
    from tm_app.application.gpt_actions.registration_guide import build_registration_guide
    from tm_app.core.catalogs import FASE_MELHORIA, PRIORIDADE_MELHORIA

    guide = build_registration_guide()
    assert "concepts" in guide
    assert guide["entity_schemas"]["instance"]["enums"]["fase_melhoria"] == list(
        FASE_MELHORIA
    )
    assert guide["entity_schemas"]["instance"]["enums"]["prioridade"] == list(
        PRIORIDADE_MELHORIA
    )
    assert guide["package_hints"]["operationId"] == "gpt_commit_improvement_package"


def test_gpt_catalog_includes_registration_guide(tm_client):
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.FilialRepository"
        ) as filial_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
        ) as setor_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
        ) as proc_cls,
    ):
        filial_cls.return_value.list_for_options.return_value = [
            {"id": "01", "label": "SC"}
        ]
        setor_cls.return_value.list_for_options.return_value = []
        proc_cls.return_value.list_distinct_tag_values.return_value = []
        response = tm_client.get("/transformometro/gpt-actions/v1/catalog")
    assert response.status_code == 200
    data = response.json()["data"]
    assert "registration_guide" in data
    assert "fase_melhoria" in data
    assert "prioridade_melhoria" in data
    assert data["registration_guide"]["entity_schemas"]["revision"]["required"]


def test_search_revisions_by_instance_id(tm_client):
    instancia_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    rows = [
        {
            "revisao_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            "instancia_id": instancia_id,
            "cenario_tipo": "baseline",
        }
    ]
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_instancia_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
        ) as rev_cls,
    ):
        rev_cls.return_value.list_by_instancia.return_value = rows
        response = tm_client.get(
            "/transformometro/gpt-actions/v1/records/revision",
            params={"instance_id": instancia_id},
        )
    assert response.status_code == 200
    body = response.json()["data"]
    assert body["total"] == 1
    assert body["items"][0]["instancia_id"] == instancia_id
    rev_cls.return_value.list_by_processo.assert_not_called()


def test_improvement_package_dry_run_incomplete(tm_client):
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/improvement-packages",
        json={"dry_run": True, "process": {"nome_processo": "X"}},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["dry_run"] is True
    assert data["ready"] is False
    assert any("instance" in m or m == "instance" for m in data["missing"])


def test_improvement_package_commit_positive():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    dispatch = MagicMock()
    dispatch.create_record.side_effect = [
        ({"processo_id": "p1"}, "ok", 201),
        ({"instancia_id": "i1"}, "ok", 201),
        ({"revisao_id": "b1"}, "ok", 201),
        ({"medicao_id": "m1"}, "ok", 200),
        ({"revisao_id": "s1"}, "ok", 201),
        ({"medicao_id": "m2"}, "ok", 200),
        ({"investimento_id": "inv1"}, "ok", 201),
    ]
    dispatch.activate_revision.return_value = {
        "revisao_id": "s1",
        "revisao_ativa": True,
    }
    dispatch.recalculate_dashboard.return_value = {"mode": "incremental"}

    svc = GuidedImprovementPackageService(dispatch)
    request = MagicMock()
    result = svc.commit(
        request,
        {
            "dry_run": False,
            "activate_scenario": True,
            "recalculate": True,
            "process": {"nome_processo": "Proc GPT", "status_processo": "ativo"},
            "instance": {
                "filial_id": "01",
                "setor_ids": ["engenharia"],
                "resumo_melhoria": "Automatizou o fechamento",
            },
            "baseline": {
                "revision": {
                    "versao_revisao": "v1.0",
                    "data_inicio_vigencia": "2026-01-01",
                },
                "measurement": {"volume_mensal": 100, "tempo_medio_execucao_min": 30},
            },
            "scenario": {
                "revision": {
                    "versao_revisao": "v2.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-03-01",
                },
                "measurement": {"volume_mensal": 100, "tempo_medio_execucao_min": 10},
                "investments": [
                    {
                        "tipo_investimento": "unico",
                        "descricao_item": "Licença RPA",
                        "valor_unitario": 5000,
                    }
                ],
            },
        },
    )
    assert result["ids"]["processo_id"] == "p1"
    assert result["ids"]["instancia_id"] == "i1"
    assert result["ids"]["baseline_revisao_id"] == "b1"
    assert result["ids"]["scenario_revisao_id"] == "s1"
    dispatch.activate_revision.assert_called_once_with(request, "s1")
    assert result["next_steps"]


def test_improvement_package_commit_reuses_existing_process_and_instance():
    """Live 20:56: KeyError('reused') was remapped to 400 not_found via LookupError."""
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    dispatch = MagicMock()
    dispatch.get_record.side_effect = lambda _req, entity, rid: {
        "process": {"processo_id": rid, "nome_processo": "Existente", "status_processo": "ativo"},
        "instance": {"instancia_id": rid, "processo_id": "p1", "status_instancia": "ativo"},
        "revision": {
            "revisao_id": rid,
            "processo_id": "p1",
            "instancia_id": "i1",
            "versao_revisao": "2.0.0",
            "cenario_tipo": "baseline",
        },
    }[entity]
    dispatch.create_record.side_effect = [
        ({"revisao_id": "s-new"}, "ok", 201),
        ({"medicao_id": "m-new"}, "ok", 200),
    ]

    svc = GuidedImprovementPackageService(dispatch)
    result = svc.commit(
        MagicMock(),
        {
            "dry_run": False,
            "process": {"id": "p1"},
            "instance": {"id": "i1"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "b1",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-14",
                    "motivo_revisao": "Teste GPT",
                },
                "measurement": {"volume_mensal": 100, "tempo_medio_execucao_min": 20},
                "investments": [],
            },
        },
    )
    assert result["reused"]["process"]["processo_id"] == "p1"
    assert result["reused"]["instance"]["instancia_id"] == "i1"
    assert result["created"]["scenario_revision"]["revisao_id"] == "s-new"
    assert result["ids"]["scenario_revisao_id"] == "s-new"
    assert dispatch.create_record.call_count == 2


def test_improvement_package_commit_missing_process_ref_is_400_not_404():
    """Live incident class: ready shape + missing process id must not return opaque 404."""
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    dispatch = MagicMock()
    dispatch.get_record.side_effect = GptActionsError("Processo não encontrado.", 404)
    svc = GuidedImprovementPackageService(dispatch)
    with pytest.raises(GptActionsError) as ei:
        svc.commit(
            MagicMock(),
            {
                "dry_run": False,
                "process": {"processo_id": "missing-process"},
                "instance": {"instancia_id": "i1"},
                "scenario": {
                    "revision": {
                        "revisao_referencia_id": "b1",
                        "versao_revisao": "2.1.0",
                        "cenario_tipo": "melhoria",
                        "data_inicio_vigencia": "2026-09-02",
                    },
                    "measurement": {"volume_mensal": 1},
                    "investments": [],
                },
            },
        )
    assert ei.value.status_code == 400
    assert ei.value.data["not_found"] == "process"
    dispatch.create_record.assert_not_called()


def test_improvement_package_commit_missing_reference_revision_is_400():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    dispatch = MagicMock()

    def _get(_request, entity, record_id):
        if entity == "revision" and record_id == "missing-ref":
            raise GptActionsError("Revisão não encontrada.", 404)
        return {"id": record_id}

    dispatch.get_record.side_effect = _get
    svc = GuidedImprovementPackageService(dispatch)
    with pytest.raises(GptActionsError) as ei:
        svc.commit(
            MagicMock(),
            {
                "dry_run": False,
                "process": {"processo_id": "p1"},
                "instance": {"instancia_id": "i1"},
                "scenario": {
                    "revision": {
                        "revisao_referencia_id": "missing-ref",
                        "versao_revisao": "2.1.0",
                        "cenario_tipo": "melhoria",
                        "data_inicio_vigencia": "2026-09-02",
                    },
                    "investments": [],
                },
            },
        )
    assert ei.value.status_code == 400
    assert ei.value.data["not_found"] == "revision"
    assert "revisao_referencia_id" in ei.value.data["field"]
    dispatch.create_record.assert_not_called()


def test_http_commit_maps_domain_404_to_400(tm_client):
    """Regression: Custom GPT disables Actions on opaque 404; commit must answer 400."""
    from tm_app.interface.http.routes import gpt_actions_routes as routes

    with patch.object(
        routes._packages,
        "commit",
        side_effect=GptActionsError("Processo não encontrado.", 404),
    ):
        response = tm_client.post(
            "/transformometro/gpt-actions/v1/improvement-packages",
            json={
                "process": {"processo_id": "p1"},
                "instance": {"instancia_id": "i1"},
                "scenario": {
                    "revision": {
                        "revisao_referencia_id": "b1",
                        "versao_revisao": "2.1.0",
                        "cenario_tipo": "melhoria",
                        "data_inicio_vigencia": "2026-09-02",
                    }
                },
            },
        )
    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    assert payload["data"]["not_found"] is True
    assert "não encontrado" in payload["message"].lower() or "not found" in payload["message"].lower()


def test_improvement_package_rejects_baseline_as_scenario():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    svc = GuidedImprovementPackageService(MagicMock())
    with pytest.raises(GptActionsError, match="incomplete"):
        svc.commit(
            MagicMock(),
            {
                "dry_run": False,
                "process": {"id": "p1"},
                "instance": {"id": "i1"},
                "scenario": {
                    "revision": {
                        "versao_revisao": "v2",
                        "cenario_tipo": "baseline",
                        "data_inicio_vigencia": "2026-01-01",
                        "revisao_referencia_id": "b1",
                    }
                },
            },
        )


def test_openapi_includes_improvement_package():
    doc = build_gpt_actions_openapi()
    assert "gpt_commit_improvement_package" in GPT_ACTIONS_OPERATION_IDS
    assert (
        "/transformometro/gpt-actions/v1/improvement-packages" in doc["paths"]
    )
    assert "gpt_get_process_context" in GPT_ACTIONS_OPERATION_IDS
    assert "/transformometro/gpt-actions/v1/process-context" in doc["paths"]
    assert "gpt_validate_improvement_package" in GPT_ACTIONS_OPERATION_IDS
    assert (
        "/transformometro/gpt-actions/v1/improvement-packages/validate" in doc["paths"]
    )
    assert count_operations(doc) == 14


def test_openapi_validate_vs_commit_consequential_flags():
    doc = build_gpt_actions_openapi()
    validate = doc["paths"][
        "/transformometro/gpt-actions/v1/improvement-packages/validate"
    ]["post"]
    commit = doc["paths"]["/transformometro/gpt-actions/v1/improvement-packages"]["post"]
    assert validate["operationId"] == "gpt_validate_improvement_package"
    assert validate["x-openai-isConsequential"] is False
    assert commit["operationId"] == "gpt_commit_improvement_package"
    assert commit["x-openai-isConsequential"] is True
    assert "Never writes" in validate["description"]
    assert "may persist" in commit["description"]
    v_schema = validate["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert v_schema.endswith("GptValidateImprovementPackageBody")
    v_props = doc["components"]["schemas"]["GptValidateImprovementPackageBody"][
        "properties"
    ]
    assert set(v_props) == {"process", "instance", "baseline", "scenario"}
    assert "dry_run" not in v_props
    assert "activate_scenario" not in v_props
    assert "recalculate" not in v_props


def test_openapi_documents_nested_improvement_package():
    doc = build_gpt_actions_openapi()
    body = doc["components"]["schemas"]["GptImprovementPackageBody"]
    props = body["properties"]
    assert "process" in props
    assert "instance" in props
    assert "scenario" in props
    assert "processo_id" in props["process"]["properties"]
    assert "instancia_id" in props["instance"]["properties"]
    scenario = props["scenario"]["properties"]
    assert "revision" in scenario
    assert "measurement" in scenario
    assert "investments" in scenario
    revision = doc["components"]["schemas"]["GptPackageRevision"]["properties"]
    assert "versao_revisao" in revision
    assert "beneficio_calculo_categoria" in revision
    assert "revisao_referencia_id" in revision
    measurement = doc["components"]["schemas"]["GptPackageMeasurement"]["properties"]
    assert "volume_mensal" in measurement
    assert "beneficio_calculo_categoria" not in measurement
    investment = doc["components"]["schemas"]["GptPackageInvestment"]["properties"]
    assert "tipo_investimento" in investment
    body_desc = body["description"]
    assert "flat" in body_desc.lower()
    commit_desc = doc["paths"]["/transformometro/gpt-actions/v1/improvement-packages"][
        "post"
    ]["description"]
    assert "persist" in commit_desc


def test_improvement_package_flat_incident_payload_not_ready(tm_client):
    """Incident-like flat scenario must not be treated as a valid package."""
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/improvement-packages",
        json={
            "dry_run": True,
            "scenario": {
                "processo_id": "11111111-1111-1111-1111-111111111111",
                "instancia_id": "22222222-2222-2222-2222-222222222222",
                "versao_revisao": "2.1.0",
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2026-09-02",
            },
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["dry_run"] is True
    assert data["ready"] is False
    missing = data["missing"]
    assert "process" in missing
    assert "instance" in missing
    assert "scenario.revision" in missing
    assert "checklist" in data


def test_improvement_package_dry_run_nested_ready_true(tm_client):
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/improvement-packages",
        json={
            "dry_run": True,
            "activate_scenario": False,
            "recalculate": False,
            "process": {"processo_id": "11111111-1111-1111-1111-111111111111"},
            "instance": {"instancia_id": "22222222-2222-2222-2222-222222222222"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "33333333-3333-3333-3333-333333333333",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_implantacao": "2026-09-02",
                    "data_inicio_vigencia": "2026-09-02",
                    "descricao_revisao": "teste",
                    "motivo_revisao": "teste",
                    "observacoes": "teste",
                    "beneficio_calculo_categoria": "automatico",
                },
                "measurement": {
                    "volume_mensal": 22,
                    "tempo_medio_execucao_min": 0.0083333333,
                    "tempo_retrabalho_min": 0,
                    "percentual_retrabalho": 0,
                    "percentual_erro": 0,
                    "quantidade_erros_mes": 0,
                    "custo_hora_mao_obra": 34.38,
                    "custo_unitario_erro": 0,
                    "custo_unitario_retrabalho": 0,
                    "custo_outros_desperdicios": 0,
                    "base_referencia_mes": "2026-09",
                    "observacoes": "teste",
                },
                "investments": [],
            },
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ready"] is True
    assert data["missing"] == []
    assert data["dry_run"] is True


def test_improvement_package_dry_run_does_not_dispatch_writes():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    dispatch = MagicMock()
    svc = GuidedImprovementPackageService(dispatch)
    result = svc.commit(
        MagicMock(),
        {
            "dry_run": True,
            "process": {"processo_id": "p1"},
            "instance": {"instancia_id": "i1"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "b1",
                    "versao_revisao": "2.1.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-09-02",
                    "beneficio_calculo_categoria": "automatico",
                },
                "measurement": {"volume_mensal": 1},
                "investments": [],
            },
        },
    )
    assert result["ready"] is True
    dispatch.create_record.assert_not_called()
    dispatch.update_record.assert_not_called()
    dispatch.activate_revision.assert_not_called()
    dispatch.recalculate_dashboard.assert_not_called()


def test_improvement_package_empty_investments_valid_on_dry_run():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    result = GuidedImprovementPackageService(MagicMock()).commit(
        MagicMock(),
        {
            "dry_run": True,
            "process": {"processo_id": "p1"},
            "instance": {"instancia_id": "i1"},
            "scenario": {
                "revision": {
                    "revisao_referencia_id": "b1",
                    "versao_revisao": "2.0.0",
                    "cenario_tipo": "melhoria",
                    "data_inicio_vigencia": "2026-01-01",
                },
                "measurement": {"volume_mensal": 10},
                "investments": [],
            },
        },
    )
    assert result["ready"] is True


def test_improvement_package_contract_drift_guide_openapi_service():
    """Guide + OpenAPI nesting must stay aligned with service expectations."""
    from tm_app.application.gpt_actions.improvement_package_contract import (
        PACKAGE_BLOCK_KEYS,
        PACKAGE_MEASUREMENT_FIELDS,
        PACKAGE_REVISION_FIELDS,
        build_package_hints,
    )
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )
    from tm_app.application.gpt_actions.registration_guide import build_registration_guide

    hints = build_registration_guide()["package_hints"]
    contract = build_package_hints()
    assert hints["canonical_package_shape"] == contract["canonical_package_shape"]
    assert hints["reuse_existing_example"]["scenario"]["revision"]
    assert set(hints["canonical_package_shape"]["scenario"]["keys"]) == set(
        PACKAGE_BLOCK_KEYS
    )

    doc = build_gpt_actions_openapi()
    scenario_props = doc["components"]["schemas"]["GptImprovementPackageBody"][
        "properties"
    ]["scenario"]["properties"]
    assert set(scenario_props) == set(PACKAGE_BLOCK_KEYS)

    openapi_rev = set(
        doc["components"]["schemas"]["GptPackageRevision"]["properties"]
    )
    assert set(PACKAGE_REVISION_FIELDS).issubset(openapi_rev)
    openapi_meas = set(
        doc["components"]["schemas"]["GptPackageMeasurement"]["properties"]
    )
    assert set(PACKAGE_MEASUREMENT_FIELDS).issubset(openapi_meas)

    # Service treats flat scenario as missing scenario.revision (no silent normalize).
    flat = GuidedImprovementPackageService(MagicMock()).commit(
        MagicMock(),
        {
            "dry_run": True,
            "scenario": {"versao_revisao": "2.1.0", "processo_id": "p"},
        },
    )
    assert flat["ready"] is False
    assert "scenario.revision" in flat["missing"]
    assert "process" in flat["missing"]
    assert "instance" in flat["missing"]


_NESTED_READY_PACKAGE = {
    "process": {"processo_id": "11111111-1111-1111-1111-111111111111"},
    "instance": {"instancia_id": "22222222-2222-2222-2222-222222222222"},
    "scenario": {
        "revision": {
            "revisao_referencia_id": "33333333-3333-3333-3333-333333333333",
            "versao_revisao": "2.1.0",
            "cenario_tipo": "melhoria",
            "data_inicio_vigencia": "2026-09-02",
            "beneficio_calculo_categoria": "automatico",
        },
        "measurement": {"volume_mensal": 22},
        "investments": [],
    },
}


def test_validate_improvement_package_nested_ready(tm_client):
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/improvement-packages/validate",
        json=_NESTED_READY_PACKAGE,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["ready"] is True
    assert data["missing"] == []
    assert data["dry_run"] is True
    assert data["hints"]["activate_scenario"] is False
    assert data["hints"]["recalculate"] is False


def test_validate_improvement_package_incomplete_ready_false(tm_client):
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/improvement-packages/validate",
        json={"process": {"nome_processo": "X"}},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ready"] is False
    assert any("instance" in m or m == "instance" for m in data["missing"])
    assert "checklist" in data


def test_validate_improvement_package_flat_scenario_not_ready(tm_client):
    response = tm_client.post(
        "/transformometro/gpt-actions/v1/improvement-packages/validate",
        json={
            "scenario": {
                "processo_id": "11111111-1111-1111-1111-111111111111",
                "instancia_id": "22222222-2222-2222-2222-222222222222",
                "versao_revisao": "2.1.0",
            }
        },
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ready"] is False
    assert "process" in data["missing"]
    assert "instance" in data["missing"]
    assert "scenario.revision" in data["missing"]


def test_validate_improvement_package_never_dispatches_writes():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    dispatch = MagicMock()
    svc = GuidedImprovementPackageService(dispatch)
    result = svc.validate(MagicMock(), _NESTED_READY_PACKAGE)
    assert result["ready"] is True
    dispatch.create_record.assert_not_called()
    dispatch.update_record.assert_not_called()
    dispatch.delete_record.assert_not_called()
    dispatch.activate_revision.assert_not_called()
    dispatch.recalculate_dashboard.assert_not_called()


def test_validate_improvement_package_ignores_malicious_write_flags(tm_client):
    dispatch_path = (
        "tm_app.interface.http.routes.gpt_actions_routes._packages._dispatch"
    )
    with patch(dispatch_path) as dispatch:
        response = tm_client.post(
            "/transformometro/gpt-actions/v1/improvement-packages/validate",
            json={
                **_NESTED_READY_PACKAGE,
                "dry_run": False,
                "activate_scenario": True,
                "recalculate": True,
            },
        )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["ready"] is True
    assert data["hints"]["activate_scenario"] is False
    assert data["hints"]["recalculate"] is False
    dispatch.create_record.assert_not_called()
    dispatch.update_record.assert_not_called()
    dispatch.delete_record.assert_not_called()
    dispatch.activate_revision.assert_not_called()
    dispatch.recalculate_dashboard.assert_not_called()


def test_validate_and_commit_dry_run_checklists_match():
    from tm_app.application.gpt_actions.improvement_package_service import (
        GuidedImprovementPackageService,
    )

    svc = GuidedImprovementPackageService(MagicMock())
    request = MagicMock()
    validated = svc.validate(request, _NESTED_READY_PACKAGE)
    dry = svc.commit(request, {**_NESTED_READY_PACKAGE, "dry_run": True})
    assert validated["ready"] == dry["ready"]
    assert validated["missing"] == dry["missing"]
    assert validated["checklist"] == dry["checklist"]


def _process_context_patches():
    return [
        patch(
            "tm_app.application.gpt_actions.process_context_service.require_transformometro_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.check_processo_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.check_instancia_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.ProcessoRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.ProcessoInstanciaRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.RevisaoRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.MedicaoRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.InvestimentoRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.VinculoRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.ProcessoDiagramRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.ProcessoDecomposicaoRepository"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.ProcessRevisionCompareService"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.RevisaoImpactEffortMatrixService"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.DiagramaCompositionService"
        ),
        patch(
            "tm_app.application.gpt_actions.process_context_service.DecomposicaoCompositionService"
        ),
    ]


def _enter_process_context_patches(stack: ExitStack):
    return tuple(stack.enter_context(p) for p in _process_context_patches())


def test_process_context_positive():
    from tm_app.application.gpt_actions.process_context_service import (
        ProcessContextService,
    )

    request = MagicMock()
    with ExitStack() as stack:
        (
            _view,
            _proc_view,
            _inst_view,
            proc_cls,
            inst_cls,
            rev_cls,
            med_cls,
            inv_cls,
            vin_cls,
            diag_cls,
            decomp_cls,
            cmp_cls,
            _matrix,
            dcomp_cls,
            _decomp_comp,
        ) = _enter_process_context_patches(stack)
        stack.enter_context(
            patch(
                "tm_app.application.gpt_actions.process_context_service.filter_rows_for_access",
                side_effect=lambda _req, rows, **_kw: rows,
            )
        )
        pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
        iid = "iiiiiiii-iiii-iiii-iiii-iiiiiiiiiiii"
        bid = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        sid = "ssssssss-ssss-ssss-ssss-ssssssssssss"
        proc_cls.return_value.get.return_value = {
            "processo_id": pid,
            "nome_processo": "Fechamento",
            "status_processo": "ativo",
        }
        inst_cls.return_value.list_by_processo.return_value = [
            {
                "instancia_id": iid,
                "processo_id": pid,
                "codigo_filial": "01",
                "resumo_melhoria": "Automação",
            }
        ]
        rev_cls.return_value.list_by_processo.return_value = [
            {
                "revisao_id": bid,
                "processo_id": pid,
                "instancia_id": iid,
                "cenario_tipo": "baseline",
                "versao_revisao": "v1",
                "data_inicio_vigencia": "2026-01-01",
                "revisao_ativa": False,
            },
            {
                "revisao_id": sid,
                "processo_id": pid,
                "instancia_id": iid,
                "cenario_tipo": "melhoria",
                "versao_revisao": "v2",
                "data_inicio_vigencia": "2026-03-01",
                "revisao_referencia_id": bid,
                "revisao_ativa": True,
            },
        ]
        med_cls.return_value.get_by_revisao.side_effect = lambda rid: {
            "medicao_id": f"m-{rid[:4]}",
            "revisao_id": rid,
            "volume_mensal": 10,
        }
        inv_cls.return_value.list_by_revisao.return_value = []
        vin_cls.return_value.list_by_revisao.return_value = []
        diag_cls.return_value.get.return_value = {
            "conteudo": {"format": "flowchart_v1", "nodes": [{"id": "n1"}]}
        }
        decomp_cls.return_value.get.return_value = None
        cmp_cls.return_value.compare.return_value = {
            "total_revisoes": 2,
            "items": [{"revisao_id": bid}, {"revisao_id": sid}],
        }
        dcomp_cls.return_value.compose_for_processo.return_value = {
            "mermaid": "flowchart TD; A-->B"
        }

        result = ProcessContextService().get_context(request, process_id=pid)

    assert result["context_version"] == "process_intelligence_context_v1"
    assert "capabilities" not in result
    assert result["surface_supports"]["side_effect"] is False
    assert result["surface_supports"]["persist_diagram_via_gpt"] is True
    assert result["surface_supports"]["persist_decomposition_via_gpt"] is True
    assert "write_records" not in result["surface_supports"]
    assert result["as_is"]["role"] == "AS_IS"
    assert result["as_is"]["mermaid"] is None
    assert result["as_is"]["diagram"]["epistemic_status"] == "UNKNOWN"
    assert result["current_composed"]["role"] == "CURRENT_COMPOSED"
    assert result["current_composed"]["mermaid"] == "flowchart TD; A-->B"
    assert result["process"]["visible_scope_stats"]["instancia_count"] == 1
    assert "setup_stats" not in result["process"]
    dcomp_cls.return_value.compose_for_processo.assert_called_once()
    assert (
        dcomp_cls.return_value.compose_for_processo.call_args.kwargs["instancia_id"]
        == iid
    )
    assert any(n["type"] == "process" for n in result["process_graph"]["nodes"])
    assert any(e["type"] == "has_instance" for e in result["process_graph"]["edges"])
    assert any(e["type"] == "references" for e in result["process_graph"]["edges"])
    assert "decomposition_tree" in result["data_quality"]["missing"]
    assert result["as_is"]["epistemic_status"] == "OBSERVED"


def test_process_context_hides_forbidden_branch_instance_and_comparison():
    from tm_app.application.gpt_actions.process_context_service import (
        ProcessContextService,
    )

    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    iid_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    iid_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    rid_a = "raaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    rid_b = "rbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    def _filter_visible(_req, rows, **_kw):
        return [r for r in rows if str(r.get("codigo_filial")) == "01"]

    with ExitStack() as stack:
        (
            _view,
            _proc_view,
            _inst_view,
            proc_cls,
            inst_cls,
            rev_cls,
            med_cls,
            inv_cls,
            vin_cls,
            diag_cls,
            decomp_cls,
            cmp_cls,
            matrix_cls,
            dcomp_cls,
            decomp_comp_cls,
        ) = _enter_process_context_patches(stack)
        stack.enter_context(
            patch(
                "tm_app.application.gpt_actions.process_context_service.filter_rows_for_access",
                side_effect=_filter_visible,
            )
        )
        proc_cls.return_value.get.return_value = {
            "processo_id": pid,
            "nome_processo": "Proc",
        }
        inst_cls.return_value.list_by_processo.return_value = [
            {
                "instancia_id": iid_a,
                "processo_id": pid,
                "codigo_filial": "01",
                "resumo_melhoria": "A",
            },
            {
                "instancia_id": iid_b,
                "processo_id": pid,
                "codigo_filial": "02",
                "resumo_melhoria": "B forbidden",
            },
        ]
        rev_cls.return_value.list_by_processo.return_value = [
            {
                "revisao_id": rid_a,
                "processo_id": pid,
                "instancia_id": iid_a,
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2026-01-01",
            },
            {
                "revisao_id": rid_b,
                "processo_id": pid,
                "instancia_id": iid_b,
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2026-02-01",
                "revisao_ativa": True,
            },
        ]
        med_cls.return_value.get_by_revisao.return_value = None
        inv_cls.return_value.list_by_revisao.return_value = []
        vin_cls.return_value.list_by_revisao.return_value = []
        diag_cls.return_value.get.return_value = None
        decomp_cls.return_value.get.return_value = None
        cmp_cls.return_value.compare.return_value = {
            "total_revisoes": 2,
            "items": [
                {"revisao_id": rid_a, "cenario_tipo": "baseline"},
                {"revisao_id": rid_b, "cenario_tipo": "melhoria"},
            ],
        }
        dcomp_cls.return_value.compose_for_processo.return_value = {
            "mermaid": "SAFE_A_ONLY"
        }
        decomp_comp_cls.return_value.compose_for_processo.return_value = {}

        result = ProcessContextService().get_context(request, process_id=pid)

    instance_ids = {i["instancia_id"] for i in result["instances"]}
    revision_ids = {r["revisao_id"] for r in result["revisions"]}
    compare_ids = {i["revisao_id"] for i in result["comparison"]["items"]}
    assert iid_a in instance_ids
    assert iid_b not in instance_ids
    assert rid_b not in revision_ids
    assert rid_b not in compare_ids
    assert result["comparison"]["total_revisoes"] == 1
    assert result["process"]["visible_scope_stats"]["instancia_count"] == 1
    assert result["current_composed"]["mermaid"] == "SAFE_A_ONLY"
    dcomp_cls.return_value.compose_for_processo.assert_called_once()
    assert (
        dcomp_cls.return_value.compose_for_processo.call_args.kwargs["instancia_id"]
        == iid_a
    )
    matrix_cls.return_value.build_for_instancia.assert_called_once_with(iid_a)


def test_process_context_forbidden_overlay_not_composed_without_instance():
    from tm_app.application.gpt_actions.process_context_service import (
        ProcessContextService,
    )

    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    iid_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    iid_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    with ExitStack() as stack:
        (
            _view,
            _proc_view,
            _inst_view,
            proc_cls,
            inst_cls,
            rev_cls,
            med_cls,
            inv_cls,
            vin_cls,
            diag_cls,
            decomp_cls,
            cmp_cls,
            _matrix,
            dcomp_cls,
            decomp_comp_cls,
        ) = _enter_process_context_patches(stack)
        stack.enter_context(
            patch(
                "tm_app.application.gpt_actions.process_context_service.filter_rows_for_access",
                side_effect=lambda _req, rows, **_kw: rows,
            )
        )
        proc_cls.return_value.get.return_value = {"processo_id": pid, "nome_processo": "P"}
        inst_cls.return_value.list_by_processo.return_value = [
            {"instancia_id": iid_a, "processo_id": pid, "codigo_filial": "01"},
            {"instancia_id": iid_b, "processo_id": pid, "codigo_filial": "01"},
        ]
        rev_cls.return_value.list_by_processo.return_value = [
            {
                "revisao_id": "r1",
                "instancia_id": iid_a,
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2026-01-01",
            },
            {
                "revisao_id": "r2",
                "instancia_id": iid_b,
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2026-02-01",
                "revisao_ativa": True,
            },
        ]
        med_cls.return_value.get_by_revisao.return_value = None
        inv_cls.return_value.list_by_revisao.return_value = []
        vin_cls.return_value.list_by_revisao.return_value = []
        diag_cls.return_value.get.return_value = {"conteudo": {"nodes": []}}
        decomp_cls.return_value.get.return_value = None
        cmp_cls.return_value.compare.return_value = {"items": [], "total_revisoes": 0}

        result = ProcessContextService().get_context(request, process_id=pid)

    assert result["selection"]["requires_instance_selection"] is True
    assert result["selection"]["baseline_revisao_id"] is None
    assert result["selection"]["scenario_revisao_id"] is None
    assert "requires_instance_selection" in result["data_quality"]["ambiguities"]
    assert result["current_composed"]["mermaid"] is None
    assert result["current_composed"]["epistemic_status"] == "UNKNOWN"
    dcomp_cls.return_value.compose_for_processo.assert_not_called()
    decomp_comp_cls.return_value.compose_for_processo.assert_not_called()


def test_process_context_revision_id_constrains_instance_selection():
    from tm_app.application.gpt_actions.process_context_service import (
        ProcessContextService,
    )

    request = MagicMock()
    pid = "pppppppp-pppp-pppp-pppp-pppppppppppp"
    iid_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    iid_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    base_a = "baaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    scen_a = "saaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    base_b = "bbbbbbbb-1111-1111-1111-bbbbbbbbbbbb"
    scen_b = "sbbbbbbb-2222-2222-2222-bbbbbbbbbbbb"

    with ExitStack() as stack:
        (
            _view,
            _proc_view,
            _inst_view,
            proc_cls,
            inst_cls,
            rev_cls,
            med_cls,
            inv_cls,
            vin_cls,
            diag_cls,
            decomp_cls,
            cmp_cls,
            _matrix,
            dcomp_cls,
            _decomp_comp,
        ) = _enter_process_context_patches(stack)
        stack.enter_context(
            patch(
                "tm_app.application.gpt_actions.process_context_service.filter_rows_for_access",
                side_effect=lambda _req, rows, **_kw: rows,
            )
        )
        proc_cls.return_value.get.return_value = {"processo_id": pid, "nome_processo": "P"}
        inst_cls.return_value.list_by_processo.return_value = [
            {"instancia_id": iid_a, "processo_id": pid, "codigo_filial": "01"},
            {"instancia_id": iid_b, "processo_id": pid, "codigo_filial": "01"},
        ]
        rev_cls.return_value.list_by_processo.return_value = [
            {
                "revisao_id": base_a,
                "instancia_id": iid_a,
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2026-01-01",
            },
            {
                "revisao_id": scen_a,
                "instancia_id": iid_a,
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2026-03-01",
                "revisao_referencia_id": base_a,
                "revisao_ativa": True,
            },
            {
                "revisao_id": base_b,
                "instancia_id": iid_b,
                "cenario_tipo": "baseline",
                "data_inicio_vigencia": "2026-01-01",
            },
            {
                "revisao_id": scen_b,
                "instancia_id": iid_b,
                "cenario_tipo": "melhoria",
                "data_inicio_vigencia": "2026-04-01",
                "revisao_referencia_id": base_b,
                "revisao_ativa": True,
            },
        ]
        med_cls.return_value.get_by_revisao.return_value = None
        inv_cls.return_value.list_by_revisao.return_value = []
        vin_cls.return_value.list_by_revisao.return_value = []
        diag_cls.return_value.get.return_value = None
        decomp_cls.return_value.get.return_value = None
        cmp_cls.return_value.compare.return_value = {
            "items": [
                {"revisao_id": base_a},
                {"revisao_id": scen_a},
                {"revisao_id": base_b},
                {"revisao_id": scen_b},
            ],
            "total_revisoes": 4,
        }
        dcomp_cls.return_value.compose_for_processo.return_value = {
            "mermaid": "INSTANCE_A"
        }

        result = ProcessContextService().get_context(
            request, process_id=pid, revision_id=scen_a
        )

    assert result["selection"]["instance_id"] == iid_a
    assert result["selection"]["baseline_revisao_id"] == base_a
    assert result["selection"]["scenario_revisao_id"] == scen_a
    assert {i["instancia_id"] for i in result["instances"]} == {iid_a}
    assert {r["revisao_id"] for r in result["revisions"]} == {base_a, scen_a}
    assert {i["revisao_id"] for i in result["comparison"]["items"]} == {base_a, scen_a}
    assert result["comparison"]["total_revisoes"] == 2
    assert result["as_is"]["mermaid"] is None
    assert result["current_composed"]["mermaid"] == "INSTANCE_A"


def test_process_context_view_only_surface_does_not_claim_write_auth():
    from tm_app.application.gpt_actions.process_context_service import (
        ProcessContextService,
    )

    request = MagicMock()
    with ExitStack() as stack:
        (
            _view,
            _proc_view,
            _inst_view,
            proc_cls,
            inst_cls,
            rev_cls,
            med_cls,
            inv_cls,
            vin_cls,
            diag_cls,
            decomp_cls,
            cmp_cls,
            _matrix,
            dcomp_cls,
            _decomp_comp,
        ) = _enter_process_context_patches(stack)
        stack.enter_context(
            patch(
                "tm_app.application.gpt_actions.process_context_service.filter_rows_for_access",
                side_effect=lambda _req, rows, **_kw: rows,
            )
        )
        proc_cls.return_value.get.return_value = {
            "processo_id": "pppppppp-pppp-pppp-pppp-pppppppppppp",
            "nome_processo": "P",
        }
        inst_cls.return_value.list_by_processo.return_value = []
        rev_cls.return_value.list_by_processo.return_value = []
        med_cls.return_value.get_by_revisao.return_value = None
        inv_cls.return_value.list_by_revisao.return_value = []
        vin_cls.return_value.list_by_revisao.return_value = []
        diag_cls.return_value.get.return_value = None
        decomp_cls.return_value.get.return_value = None
        cmp_cls.return_value.compare.return_value = {"items": [], "total_revisoes": 0}

        result = ProcessContextService().get_context(
            request, process_id="pppppppp-pppp-pppp-pppp-pppppppppppp"
        )

    supports = result["surface_supports"]
    assert supports["records_api"] is True
    assert supports["improvement_package_api"] is True
    assert "write_records" not in supports
    assert "write_improvement_package" not in supports
    assert "authorization" in supports["support_vs_authorization"].lower()


def test_process_context_forbidden_without_view():
    from tests.support import test_app as support

    client = _gpt_client_without_universal_mocks()
    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = []
    try:
        response = client.get(
            "/transformometro/gpt-actions/v1/process-context",
            params={"process_id": "pppppppp-pppp-pppp-pppp-pppppppppppp"},
        )
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms
    assert response.status_code == 403


def test_process_context_missing_process_id(tm_client):
    response = tm_client.get("/transformometro/gpt-actions/v1/process-context")
    assert response.status_code in {400, 422}


def test_resolve_setor_codigo_accepts_uuid_and_business_code():
    from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService

    svc = GptActionsDispatchService()
    setor_uuid = "293ebdef-16f5-4691-bac0-627f8e55c7bf"
    row = {
        "setor_id": setor_uuid,
        "codigo_setor": "comercial",
        "nome_setor": "Comercial",
    }
    with patch(
        "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
    ) as setor_cls:
        setor_cls.return_value.get.return_value = row
        assert svc._resolve_setor_codigo(setor_uuid) == "comercial"
        assert svc._resolve_setor_codigo("comercial") == "comercial"
        assert setor_cls.return_value.get.call_count == 2


def test_resolve_setor_codigo_unknown_is_400():
    from tm_app.application.gpt_actions.dispatch_service import (
        GptActionsDispatchService,
        GptActionsError,
    )

    svc = GptActionsDispatchService()
    with patch(
        "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
    ) as setor_cls:
        setor_cls.return_value.get.return_value = None
        with pytest.raises(GptActionsError) as exc:
            svc._resolve_setor_codigo("departamento-inexistente")
    assert exc.value.status_code == 400
    assert "department" in exc.value.message.lower()


def test_search_process_resolves_setor_uuid_to_codigo_before_list():
    from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService

    request = MagicMock()
    setor_uuid = "293ebdef-16f5-4691-bac0-627f8e55c7bf"
    process_row = {
        "processo_id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        "nome_processo": "Acompanhamentos dos Pedidos de Venda",
        "codigo_processo": "PROC-0008",
    }
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
        ) as setor_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
        ) as proc_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.filter_rows_for_access",
            side_effect=lambda _req, rows, **_kw: rows,
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoSetupStatsService"
        ) as stats_cls,
    ):
        setor_cls.return_value.get.return_value = {
            "setor_id": setor_uuid,
            "codigo_setor": "comercial",
        }
        proc_cls.return_value.list.return_value = [process_row]
        stats_cls.return_value.enrich_processos.side_effect = lambda rows: rows

        via_uuid = GptActionsDispatchService().search_records(
            request, "process", setor_id=setor_uuid
        )
        via_code = GptActionsDispatchService().search_records(
            request, "process", setor_id="comercial"
        )

    assert via_uuid["total"] == via_code["total"] == 1
    assert proc_cls.return_value.list.call_args_list[0].kwargs["setor_id"] == "comercial"
    assert proc_cls.return_value.list.call_args_list[1].kwargs["setor_id"] == "comercial"


def test_search_process_unknown_setor_does_not_silent_zero():
    from tm_app.application.gpt_actions.dispatch_service import (
        GptActionsDispatchService,
        GptActionsError,
    )

    request = MagicMock()
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.SetorRepository"
        ) as setor_cls,
        patch(
            "tm_app.application.gpt_actions.dispatch_service.ProcessoRepository"
        ) as proc_cls,
    ):
        setor_cls.return_value.get.return_value = None
        with pytest.raises(GptActionsError) as exc:
            GptActionsDispatchService().search_records(
                request, "process", setor_id="departamento-inexistente"
            )
    assert exc.value.status_code == 400
    proc_cls.return_value.list.assert_not_called()


def test_analyze_instances_honors_processo_id():
    from tm_app.application.gpt_actions.dispatch_service import GptActionsDispatchService

    request = MagicMock()
    pid_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    snapshot = MagicMock()
    snapshot.instancias.return_value = {
        "total": 1,
        "items": [{"processo_id": pid_a, "instancia_id": "i1"}],
    }
    with (
        patch(
            "tm_app.application.gpt_actions.dispatch_service.require_transformometro_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.check_dashboard_filial_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.dispatch_service.DashboardSnapshotReadService",
            return_value=snapshot,
        ),
    ):
        result = GptActionsDispatchService().analyze(
            request,
            view="instances",
            processo_id=pid_a,
        )
    snapshot.instancias.assert_called_once()
    assert snapshot.instancias.call_args.kwargs["processo_id"] == pid_a
    assert result["total"] == 1
    assert all(i["processo_id"] == pid_a for i in result["items"])


def test_openapi_setor_id_documents_uuid_or_code_and_stable_surface():
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == 14
    assert "gpt_get_process_context" in GPT_ACTIONS_OPERATION_IDS
    assert "gpt_analyze" in GPT_ACTIONS_OPERATION_IDS
    analysis = doc["paths"]["/transformometro/gpt-actions/v1/analysis"]["get"]
    setor = next(p for p in analysis["parameters"] if p["name"] == "setor_id")
    assert "UUID" in setor["description"]
    assert "codigo_setor" in setor["description"]
    assert any(p["name"] == "processo_id" for p in analysis["parameters"])
    search = doc["paths"]["/transformometro/gpt-actions/v1/records/{entity}"]["get"]
    search_setor = next(p for p in search["parameters"] if p["name"] == "setor_id")
    assert "UUID" in search_setor["description"]


def test_specialist_instructions_discovery_and_mermaid_contract():
    from pathlib import Path

    text = Path("docs/gpt-actions/specialist-instructions.md").read_text(encoding="utf-8")
    assert "compact phrase" in text
    assert "pesquisáveis e autorizados" in text
    assert "peça escolha" in text or "silent selection" in text
    assert "setor_id" in text and "comercial" in text
    assert "mermaid" in text.lower()
    assert "draft" in text.lower()
    assert "não existe" in text.lower()
    assert "svg" in text.lower()
    assert "progressive" in text.lower() or "STEP1" in text or "STEP2" in text
    assert "canonical_package_shape" in text or "scenario.revision" in text
    assert "ready=false" in text
    assert "não invente shape" in text.lower() or "Não invente shape" in text
    assert "gpt_validate_improvement_package" in text
    assert "VALIDATE != WRITE" in text


def test_openapi_all_write_actions_have_typed_examples():
    """Every mutating Action must expose concrete request examples for Custom GPT."""
    doc = build_gpt_actions_openapi()
    checks = [
        (
            "/transformometro/gpt-actions/v1/records/{entity}",
            "post",
            True,
            True,
        ),
        (
            "/transformometro/gpt-actions/v1/records/{entity}/{id}",
            "put",
            True,
            True,
        ),
        (
            "/transformometro/gpt-actions/v1/records/{entity}/{id}/duplicate",
            "post",
            True,
            True,
        ),
        (
            "/transformometro/gpt-actions/v1/dashboard/recalculate",
            "post",
            True,
            True,
        ),
        (
            "/transformometro/gpt-actions/v1/meeting-minutes/{id}/workflow",
            "post",
            True,
            True,
        ),
        (
            "/transformometro/gpt-actions/v1/improvement-packages/validate",
            "post",
            False,
            True,
        ),
        (
            "/transformometro/gpt-actions/v1/improvement-packages",
            "post",
            True,
            True,
        ),
    ]
    for path, method, consequential, require_example in checks:
        spec = doc["paths"][path][method]
        assert spec.get("x-openai-isConsequential") is consequential
        if require_example:
            media = spec["requestBody"]["content"]["application/json"]
            assert "example" in media
            assert "schema" in media
            schema = media["schema"]
            if "$ref" not in schema and schema.get("type") == "object":
                assert "properties" in schema, path
    # no-body writes stay consequential; OpenAI rejects object schema without properties
    for path, method in (
        ("/transformometro/gpt-actions/v1/records/{entity}/{id}", "delete"),
        ("/transformometro/gpt-actions/v1/revisions/{id}/activate", "post"),
    ):
        spec = doc["paths"][path][method]
        assert spec["x-openai-isConsequential"] is True
        assert "requestBody" not in spec

    schemas = doc["components"]["schemas"]
    assert "nome_processo" in schemas["GptRecordBody"]["properties"]["data"]["properties"]
    assert "GptRecalculateBody" in schemas
    assert "GptMeetingMinuteWorkflowBody" in schemas
    assert "action" in schemas["GptMeetingMinuteWorkflowBody"]["properties"]
    create_examples = doc["paths"]["/transformometro/gpt-actions/v1/records/{entity}"][
        "post"
    ]["requestBody"]["content"]["application/json"]["examples"]
    assert "instance_create" in create_examples
    assert "revision_create" in create_examples
    assert "measurement_upsert" in create_examples
    assert "investment_create" in create_examples
    commit_ex = doc["paths"]["/transformometro/gpt-actions/v1/improvement-packages"][
        "post"
    ]["requestBody"]["content"]["application/json"]["example"]
    assert "process" in commit_ex and "scenario" in commit_ex
    assert commit_ex.get("dry_run") is False

    # OpenAI Custom GPT: every inline object schema must declare properties
    def _assert_object_schemas_have_properties(node: object, path: str = "") -> None:
        if isinstance(node, dict):
            if node.get("type") == "object" and "$ref" not in node:
                assert "properties" in node, path
            for key, value in node.items():
                _assert_object_schemas_have_properties(value, f"{path}/{key}")
        elif isinstance(node, list):
            for idx, value in enumerate(node):
                _assert_object_schemas_have_properties(value, f"{path}[{idx}]")

    _assert_object_schemas_have_properties(doc)


def test_openapi_validate_non_consequential_commit_consequential():
    """CASO 9–10: validate remains no-write/non-consequential; commit stays consequential."""
    doc = build_gpt_actions_openapi()
    assert count_operations(doc) == 14
    validate = doc["paths"]["/transformometro/gpt-actions/v1/improvement-packages/validate"][
        "post"
    ]
    commit = doc["paths"]["/transformometro/gpt-actions/v1/improvement-packages"]["post"]
    assert validate["operationId"] == "gpt_validate_improvement_package"
    assert commit["operationId"] == "gpt_commit_improvement_package"
    assert validate["x-openai-isConsequential"] is False
    assert commit["x-openai-isConsequential"] is True
    # Never weaken commit consequential flag to accommodate runtime flakes.
    assert commit.get("x-openai-isConsequential") is not False


def test_specialist_instructions_never_equate_ready_or_attempt_with_saved():
    from pathlib import Path

    text = Path("docs/gpt-actions/specialist-instructions.md").read_text(encoding="utf-8")
    assert "ready=true != saved" in text
    assert "COMMIT_ATTEMPTED" in text
    assert "não afirme salvo" in text.lower() or "não afirme salvo/cadastrado" in text.lower()
    # Must not teach dangerous equivalences.
    forbidden_snippets = [
        "ready=true = saved",
        "ready=true means saved",
        "confirmation = authorization",
        "commit attempted = persisted",
    ]
    lowered = text.lower()
    for snippet in forbidden_snippets:
        assert snippet not in lowered

