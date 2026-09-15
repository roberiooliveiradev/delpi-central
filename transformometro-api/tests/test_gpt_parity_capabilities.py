"""TM-GPI-006 — user-parity Actions (evidence, timeline, reajuste, MM manage)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
    build_gpt_actions_openapi,
)


def _request() -> MagicMock:
    req = MagicMock()
    req.headers = {"Authorization": "Bearer test"}
    req.state.user = MagicMock()
    return req


def test_parity_operation_ids_in_openapi_and_builder():
    expected = {
        "gpt_list_evidence",
        "gpt_manage_evidence",
        "gpt_get_process_timeline",
        "gpt_adjust_shared_resource_cost",
        "gpt_meeting_minute_manage",
    }
    assert expected <= set(GPT_ACTIONS_OPERATION_IDS)
    doc = build_gpt_actions_openapi()
    found = {
        method["operationId"]
        for path in doc["paths"].values()
        for method in path.values()
        if isinstance(method, dict) and "operationId" in method
    }
    assert expected <= found
    assert "GptEvidenceManageBody" in doc["components"]["schemas"]
    assert "GptAdjustSharedResourceCostBody" in doc["components"]["schemas"]
    assert "GptMeetingMinuteManageBody" in doc["components"]["schemas"]


def test_list_evidence_process_requires_view_authz():
    svc = GptActionsDispatchService()
    request = _request()
    denied = MagicMock()
    denied.status_code = 403

    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.check_processo_view_access",
            return_value=denied,
        ),
    ):
        proc.return_value.get.return_value = {"processo_id": "p1"}
        with pytest.raises(GptActionsError) as exc:
            svc.list_evidence(request, scope="process", parent_id="p1")
    assert exc.value.status_code == 403


def test_list_evidence_process_positive():
    svc = GptActionsDispatchService()
    request = _request()
    row = {
        "arquivo_id": "a1",
        "tipo": "link",
        "url_externa": "https://example.com/x",
        "descricao": "doc",
        "nome_armazenado": None,
    }
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.check_processo_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoArquivoRepository"
        ) as repo,
    ):
        proc.return_value.get.return_value = {"processo_id": "p1"}
        repo.return_value.list_by_processo.return_value = [row]
        data = svc.list_evidence(request, scope="process", parent_id="p1")
    assert data["total"] == 1
    assert data["items"][0]["is_external_link"] is True
    assert data["binary_upload"] is False
    assert "nome_armazenado" not in data["items"][0]


def test_manage_evidence_rejects_scope_cross_and_delete_without_confirm():
    svc = GptActionsDispatchService()
    request = _request()
    with pytest.raises(GptActionsError) as exc:
        svc.manage_evidence(
            request,
            scope="other",
            operation="create_link",
            parent_id="p1",
            url_externa="https://x",
        )
    assert exc.value.status_code == 400

    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.check_processo_manage_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoArquivoRepository"
        ),
    ):
        proc.return_value.get.return_value = {"processo_id": "p1"}
        with pytest.raises(GptActionsError) as exc2:
            svc.manage_evidence(
                request,
                scope="process",
                operation="delete",
                parent_id="p1",
                evidence_id="a1",
                confirm_delete=False,
            )
    assert "confirm_delete" in exc2.value.message


def test_manage_evidence_create_link_process_with_readback():
    svc = GptActionsDispatchService()
    request = _request()
    created = {
        "arquivo_id": "a1",
        "tipo": "link",
        "url_externa": "https://example.com/e",
        "descricao": "link",
    }
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.check_processo_manage_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoArquivoRepository"
        ) as repo,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.touch_processo_updated_at"
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.actor_from_request",
            return_value=("u1", "u@x", "U"),
        ),
        patch.object(svc, "_audit"),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.notify_entity_updated"
        ),
    ):
        proc.return_value.get.return_value = {"processo_id": "p1"}
        repo.return_value.create.return_value = created
        repo.return_value.get.return_value = created
        data = svc.manage_evidence(
            request,
            scope="process",
            operation="create_link",
            parent_id="p1",
            url_externa="https://example.com/e",
            descricao="link",
        )
    assert data["verified"] is True
    assert data["persisted"] is True
    assert data["item"]["url_externa"] == "https://example.com/e"
    create_kwargs = repo.return_value.create.call_args
    assert create_kwargs[0][1]["tipo"] == "link"


def test_manage_evidence_revision_create_link():
    svc = GptActionsDispatchService()
    request = _request()
    revisao = {
        "revisao_id": "r1",
        "processo_id": "p1",
        "instancia_id": "i1",
    }
    created = {
        "evidencia_id": "e1",
        "tipo": "link",
        "url_externa": "https://example.com/r",
    }
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RevisaoRepository"
        ) as rev,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.check_instancia_manage_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RevisaoEvidenceRepository"
        ) as repo,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.touch_processo_for_revisao"
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.actor_from_request",
            return_value=("u1", "u@x", "U"),
        ),
        patch.object(svc, "_audit"),
    ):
        rev.return_value.get.return_value = revisao
        repo.return_value.create.return_value = created
        repo.return_value.get.return_value = created
        data = svc.manage_evidence(
            request,
            scope="revision",
            operation="create_link",
            parent_id="r1",
            url_externa="https://example.com/r",
        )
    assert data["scope"] == "revision"
    assert data["verified"] is True


def test_get_process_timeline_uses_view_authz_and_audit_repo():
    svc = GptActionsDispatchService()
    request = _request()
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.ProcessoRepository"
        ) as proc,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.check_processo_view_access",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.AuditRepository"
        ) as audit,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.enrich_timeline_actor_names",
            side_effect=lambda items, **_kw: items,
        ),
    ):
        proc.return_value.get.return_value = {"processo_id": "p1"}
        audit.return_value.list_for_processo.return_value = {
            "items": [{"action": "update"}],
            "total": 1,
            "page": 1,
            "page_size": 100,
        }
        data = svc.get_process_timeline(request, processo_id="p1")
    assert data["total"] == 1
    assert data["processo_id"] == "p1"


def test_adjust_shared_resource_cost_uses_registrar_reajuste():
    svc = GptActionsDispatchService()
    request = _request()
    custo = {
        "recurso_custo_id": "c1",
        "valor_mensal": 10.0,
        "recurso_compartilhado_id": "rc1",
    }
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.require_shared_resources_manage",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RecursoRepository"
        ) as recurso,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RecursoCustoRepository"
        ) as custo_repo,
        patch(
            "tm_app.application.services.dashboard_recalc_hook_service.DashboardRecalcHookService"
        ) as hook,
        patch.object(svc, "_audit"),
    ):
        recurso.return_value.get.return_value = {"recurso_compartilhado_id": "rc1"}
        custo_repo.return_value.registrar_reajuste.return_value = custo
        custo_repo.return_value.get.return_value = custo
        data = svc.adjust_shared_resource_cost(
            request,
            recurso_compartilhado_id="rc1",
            valor_mensal=10.0,
            vigente_desde="2026-10-01",
            observacoes="reajuste",
        )
    assert data["semantic_operation"] == "registrar_reajuste"
    assert data["verified"] is True
    assert data["custo"]["valor_mensal"] == 10.0
    custo_repo.return_value.registrar_reajuste.assert_called_once()
    hook.return_value.after_global_resource_change.assert_called_once()


def test_adjust_shared_resource_cost_denied_without_manage_zero_mutation():
    svc = GptActionsDispatchService()
    request = _request()
    denied = MagicMock()
    denied.status_code = 403
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.require_shared_resources_manage",
            return_value=denied,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RecursoCustoRepository"
        ) as custo_repo,
    ):
        with pytest.raises(GptActionsError) as exc:
            svc.adjust_shared_resource_cost(
                request,
                recurso_compartilhado_id="rc1",
                valor_mensal=99.0,
                vigente_desde="2026-10-01",
            )
    assert exc.value.status_code == 403
    custo_repo.return_value.registrar_reajuste.assert_not_called()


def test_adjust_shared_resource_cost_view_only_permission_denied():
    """view-only (no shared-resources.manage) must not mutate."""
    from types import SimpleNamespace

    from tm_app.application.gpt_actions.parity_capabilities_service import (
        ParityCapabilitiesService,
    )

    request = _request()
    request.state.user = SimpleNamespace(
        id="u-view",
        is_superadmin=False,
        permissions=["transformometro.view"],
    )
    svc = ParityCapabilitiesService(
        raise_http_err=GptActionsDispatchService()._raise_http_err,
        audit=lambda *a, **k: None,
    )
    with patch(
        "tm_app.application.gpt_actions.parity_capabilities_service.RecursoCustoRepository"
    ) as custo_repo:
        with pytest.raises(GptActionsError) as exc:
            svc.adjust_shared_resource_cost(
                request,
                recurso_compartilhado_id="rc1",
                valor_mensal=50.0,
                vigente_desde="2026-10-01",
            )
    assert exc.value.status_code == 403
    assert "shared-resources.manage" in exc.value.message
    custo_repo.return_value.registrar_reajuste.assert_not_called()


def test_adjust_shared_resource_cost_invalid_resource_no_mutation():
    svc = GptActionsDispatchService()
    request = _request()
    with (
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.require_shared_resources_manage",
            return_value=None,
        ),
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RecursoRepository"
        ) as recurso,
        patch(
            "tm_app.application.gpt_actions.parity_capabilities_service.RecursoCustoRepository"
        ) as custo_repo,
    ):
        recurso.return_value.get.return_value = None
        with pytest.raises(GptActionsError) as exc:
            svc.adjust_shared_resource_cost(
                request,
                recurso_compartilhado_id="missing",
                valor_mensal=10.0,
                vigente_desde="2026-10-01",
            )
    assert exc.value.status_code == 404
    custo_repo.return_value.registrar_reajuste.assert_not_called()


def test_ui_reajuste_requires_shared_resources_manage(tm_client):
    from tests.support import test_app as support

    prev_super = support.TEST_USER.is_superadmin
    prev_perms = list(support.TEST_USER.permissions)
    support.TEST_USER.is_superadmin = False
    support.TEST_USER.permissions = ["transformometro.view"]
    try:
        with patch(
            "tm_app.interface.http.routes.crud_routes.RecursoCustoRepository"
        ) as custo_repo:
            response = tm_client.post(
                "/transformometro/recursos-compartilhados/rc1/custos/reajuste",
                json={
                    "valor_mensal": 10,
                    "vigente_desde": "2026-10-01",
                },
            )
        assert response.status_code == 403
        custo_repo.return_value.registrar_reajuste.assert_not_called()
    finally:
        support.TEST_USER.is_superadmin = prev_super
        support.TEST_USER.permissions = prev_perms


def test_gpt_adjust_cost_unauthenticated_rejected():
    from fastapi import FastAPI
    from starlette.testclient import TestClient

    from tm_app.interface.http.routes.gpt_actions_routes import router as gpt_router
    from tm_app.middleware.auth_middleware import jwt_middleware

    app = FastAPI()
    app.middleware("http")(jwt_middleware)
    app.include_router(gpt_router)
    client = TestClient(app)
    denied = client.post(
        "/transformometro/gpt-actions/v1/shared-resources/adjust-cost",
        json={
            "recurso_compartilhado_id": "rc1",
            "valor_mensal": 10,
            "vigente_desde": "2026-10-01",
        },
    )
    assert denied.status_code == 401


def test_meeting_minute_manage_resend_requires_confirm():
    svc = GptActionsDispatchService()
    request = _request()
    with patch.object(svc._parity, "_minutes") as minutes:
        with pytest.raises(GptActionsError) as exc:
            svc.manage_meeting_minute(
                request,
                action="resend",
                minute_id="m1",
                payload={},
            )
        assert "confirm_resend" in exc.value.message
        minutes.resend_sign_invites.assert_not_called()

        minutes.resend_sign_invites.return_value = {"resent_count": 1, "mail_sent": 1}
        minutes.get_detail.return_value = {
            "minute": {"id": "m1"},
            "signers": [{"status": "pending"}],
        }
        data = svc.manage_meeting_minute(
            request,
            action="resend",
            minute_id="m1",
            payload={"confirm_resend": True},
        )
    assert data["persisted"] is True
    assert data["verified"] is True
    minutes.get_detail.assert_called_once_with(request.state.user, "m1")


def test_meeting_minute_create_version_verified_only_after_readback():
    svc = GptActionsDispatchService()
    request = _request()
    with patch.object(svc._parity, "_minutes") as minutes:
        minutes.create_version.return_value = {"id": "v2", "version_id": "v2"}
        minutes.get_detail.return_value = {
            "minute": {"id": "m1"},
            "version": {"id": "v2"},
            "versions": [{"id": "v1"}, {"id": "v2"}],
        }
        data = svc.manage_meeting_minute(
            request,
            action="create_version",
            minute_id="m1",
            payload={"change_reason": "ajuste"},
        )
    assert data["persisted"] is True
    assert data["verified"] is True
    assert data["data"]["read_back"]["version"]["id"] == "v2"


def test_meeting_minute_set_signers_verified_via_get_detail():
    svc = GptActionsDispatchService()
    request = _request()
    signers = [{"user_id": "u1", "display_name": "A", "invite_email": ""}]
    with patch.object(svc._parity, "_minutes") as minutes:
        minutes.set_signers.return_value = {"signers": signers}
        minutes.get_detail.return_value = {
            "minute": {"id": "m1"},
            "signers": signers,
        }
        data = svc.manage_meeting_minute(
            request,
            action="set_signers",
            minute_id="m1",
            payload={"signers": signers},
        )
    assert data["verified"] is True
    assert "read_back" in data["data"]


def test_meeting_minute_failed_write_never_verified():
    svc = GptActionsDispatchService()
    request = _request()
    with patch.object(svc._parity, "_minutes") as minutes:
        minutes.set_participants.side_effect = ValueError("bloqueado")
        with pytest.raises(GptActionsError):
            svc.manage_meeting_minute(
                request,
                action="set_participants",
                minute_id="m1",
                payload={"participants": []},
            )
    # No successful return with verified=true — exception path only.


def test_meeting_minute_manage_generate_from_transcript_is_no_write():
    svc = GptActionsDispatchService()
    request = _request()
    with (
        patch.object(svc._parity, "_minutes") as minutes,
        patch.object(svc._parity, "_kimi") as kimi,
    ):
        minutes._assert.return_value = None
        kimi.generate_from_transcript.return_value = {
            "agenda_html": "<p>a</p>",
            "body_html": "<p>b</p>",
        }
        data = svc.manage_meeting_minute(
            request,
            action="generate_from_transcript",
            minute_id=None,
            payload={
                "unit_code": "01",
                "transcript_html": "<p>fala</p>",
            },
        )
    assert data["persisted"] is False
    assert data["derived"] is True
    assert data["provenance"] == "transcript_derived_draft"


def test_no_generic_proxy_or_binary_payload_in_parity_openapi():
    doc = build_gpt_actions_openapi()
    blob = str(doc).lower()
    assert "gpt_call_any_route" not in blob
    assert "multipart" not in blob
    assert "base64" not in blob
    manage = doc["paths"]["/transformometro/gpt-actions/v1/evidence/manage"]["post"]
    assert manage["x-openai-isConsequential"] is True


def test_http_routes_wired(tm_client):
    with (
        patch(
            "tm_app.interface.http.routes.gpt_actions_routes._dispatch.list_evidence",
            return_value={"total": 0, "items": []},
        ),
        patch(
            "tm_app.interface.http.routes.gpt_actions_routes._dispatch.get_process_timeline",
            return_value={"total": 0, "items": []},
        ),
    ):
        list_resp = tm_client.get(
            "/transformometro/gpt-actions/v1/evidence",
            params={"scope": "process", "parent_id": "p1"},
        )
        tl_resp = tm_client.get(
            "/transformometro/gpt-actions/v1/processes/p1/timeline"
        )
    assert list_resp.status_code == 200
    assert tl_resp.status_code == 200
