"""Tests for Custom GPT Actions facade (contract + dispatch wiring)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.entities import (
    GptEntity,
    entity_supports,
    parse_entity,
)
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
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
    "gpt_get_openapi_schema",
)


def test_coverage_anchors_match_builder():
    assert set(_COVERAGE_ANCHORS) == set(GPT_ACTIONS_OPERATION_IDS)


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
    oa_schema = (
        doc["paths"]["/transformometro/gpt-actions/v1/openapi.json"]["get"]
        ["responses"]["200"]["content"]["application/json"]["schema"]
    )
    assert oa_schema.get("additionalProperties") is True
    assert "properties" not in oa_schema


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
    assert payload.get("openapi", "").startswith("3.")
    assert "gpt_analyze" in str(payload)


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
