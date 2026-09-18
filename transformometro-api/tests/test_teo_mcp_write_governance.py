"""Governed write PREPARE/ACT tests for TÉO MCP."""

from __future__ import annotations

import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request

from delpi_auth.request_context import (
    reset_current_user,
    reset_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.application.governed_writes.errors import (
    FORBIDDEN,
    OUTCOME_VERIFICATION_FAILED,
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_EXPIRED,
    PROPOSAL_MISMATCH,
    PROPOSAL_REQUIRED,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import GovernedWriteOrchestrator
from tm_app.application.governed_writes.proposal_store import (
    get_proposal_store,
    mint_proposal_handle,
    reset_proposal_store_for_tests,
)
from tm_app.application.gpt_actions.dispatch_service import (
    GptActionsDispatchService,
    GptActionsError,
)
from tm_app.interface.mcp.tool_bridge import (
    tool_act_activate_revision,
    tool_act_create_record,
    tool_act_recalculate_dashboard,
    tool_commit_improvement_package,
    tool_get_catalog,
    tool_manage_evidence,
    tool_prepare_activate_revision,
    tool_prepare_create_record,
    tool_prepare_improvement_package,
    tool_prepare_recalculate_dashboard,
    tool_validate_improvement_package,
)


def _auth_user(**kwargs):
    return SimpleNamespace(
        id=kwargs.get("id", "u1"),
        email=kwargs.get("email", "teo@example.com"),
        name="Téo",
        roles=[],
        groups=[],
        permissions=kwargs.get(
            "permissions",
            ["transformometro.access"],
        ),
        is_superadmin=kwargs.get("is_superadmin", False),
    )


def _request_for(user) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/mcp",
        "raw_path": b"/mcp",
        "query_string": b"",
        "headers": [(b"authorization", b"Bearer test")],
        "client": ("127.0.0.1", 0),
        "server": ("test", 443),
    }
    request = Request(scope)
    request.state.user = user
    return request


@pytest.fixture(autouse=True)
def _clean_proposals():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


class TestGovernedOrchestrator:
    def test_prepare_success_create(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                result = orch.prepare(
                    request,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome_processo": "X"}},
                )
        assert result["proposal_handle"]
        assert result["act_allowed"] is True
        assert result["capability"] == "create_record"
        assert "exact_change" in result
        assert result["current_state_fingerprint"]

    def test_prepare_forbidden_recalculate(self):
        orch = GovernedWriteOrchestrator()
        user = _auth_user(permissions=[])
        request = _request_for(user)
        with pytest.raises(GovernedWriteError) as exc:
            orch.prepare(request, capability="recalculate_dashboard", args={})
        assert exc.value.code == FORBIDDEN
        assert exc.value.status_code == 403

    def test_prepare_validation_failure_evidence_delete(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with pytest.raises(GovernedWriteError) as exc:
            orch.prepare(
                request,
                capability="manage_evidence",
                args={
                    "scope": "process",
                    "operation": "delete",
                    "parent_id": "p1",
                    "evidence_id": "e1",
                    "confirm_delete": False,
                },
            )
        assert exc.value.code == VALIDATION

    def test_act_without_proposal(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with pytest.raises(GovernedWriteError) as exc:
            orch.act(request, capability="create_record", proposal_handle=None)
        assert exc.value.code == PROPOSAL_REQUIRED

    def test_act_expired_proposal(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome": "A"}},
                )
        handle = prepared["proposal_handle"]
        # Force expiry in store
        store = get_proposal_store()
        from tm_app.application.governed_writes.proposal_store import parse_proposal_handle

        pid = parse_proposal_handle(handle)
        proposal = store.get(pid)
        assert proposal is not None
        proposal.expires_at = time.time() - 10
        with pytest.raises(GovernedWriteError) as exc:
            orch.act(request, capability="create_record", proposal_handle=handle)
        assert exc.value.code == PROPOSAL_EXPIRED

    def test_act_different_actor(self):
        orch = GovernedWriteOrchestrator()
        request_a = _request_for(_auth_user(id="u1"))
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request_a,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome": "A"}},
                )
        request_b = _request_for(_auth_user(id="u2"))
        with pytest.raises(GovernedWriteError) as exc:
            orch.act(
                request_b,
                capability="create_record",
                proposal_handle=prepared["proposal_handle"],
            )
        assert exc.value.code == PROPOSAL_ACTOR_MISMATCH

    def test_act_altered_capability_mismatch(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome": "A"}},
                )
        with pytest.raises(GovernedWriteError) as exc:
            orch.act(
                request,
                capability="delete_record",
                proposal_handle=prepared["proposal_handle"],
            )
        assert exc.value.code == PROPOSAL_MISMATCH

    def test_act_after_state_changed(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(
            orch._dispatch,
            "get_record",
            side_effect=[
                {"id": "r1", "versao": "1"},
                {"id": "r1", "versao": "2"},  # fingerprint recompute diverges
            ],
        ):
            with patch.object(
                orch._dispatch, "_require_revisao_manage_access", return_value=None
            ):
                prepared = orch.prepare(
                    request,
                    capability="activate_revision",
                    args={"id": "r1"},
                )
            with pytest.raises(GovernedWriteError) as exc:
                orch.act(
                    request,
                    capability="activate_revision",
                    proposal_handle=prepared["proposal_handle"],
                )
        assert exc.value.code == PROPOSAL_STALE

    def test_act_forbidden_after_prepare(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(
            orch._dispatch, "get_record", return_value={"id": "r1", "ativa": False}
        ):
            with patch.object(
                orch._dispatch, "_require_revisao_manage_access", return_value=None
            ):
                prepared = orch.prepare(
                    request,
                    capability="activate_revision",
                    args={"id": "r1"},
                )
            # On ACT, AuthZ now fails
            with patch.object(
                orch._dispatch,
                "_require_revisao_manage_access",
                side_effect=GptActionsError("Sem permissão", 403),
            ):
                with patch.object(
                    orch._dispatch,
                    "activate_revision",
                    side_effect=GptActionsError("Sem permissão", 403),
                ):
                    with pytest.raises(GovernedWriteError) as exc:
                        orch.act(
                            request,
                            capability="activate_revision",
                            proposal_handle=prepared["proposal_handle"],
                        )
        assert exc.value.code == FORBIDDEN

    def test_successful_write_with_readback(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        created = {"processo_id": "p-new", "nome": "X"}
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome": "X"}},
                )
        with patch.object(
            orch._dispatch,
            "create_record",
            return_value=(created, "ok", 201),
        ):
            with patch.object(
                orch._dispatch, "get_record", return_value=created
            ):
                result = orch.act(
                    request,
                    capability="create_record",
                    proposal_handle=prepared["proposal_handle"],
                )
        assert result["verified"] is True
        assert result["data"]["id"] == "p-new"

    def test_outcome_verification_failed(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome": "X"}},
                )
        with patch.object(
            orch._dispatch,
            "create_record",
            return_value=({"processo_id": "p1"}, "ok", 201),
        ):
            with patch.object(
                orch._dispatch,
                "get_record",
                side_effect=GptActionsError("missing", 404),
            ):
                with pytest.raises(GovernedWriteError) as exc:
                    orch.act(
                        request,
                        capability="create_record",
                        proposal_handle=prepared["proposal_handle"],
                    )
        assert exc.value.code == OUTCOME_VERIFICATION_FAILED

    def test_proposal_replay_consumed(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        created = {"processo_id": "p-new"}
        with patch.object(orch._dispatch, "_require_capability"):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request,
                    capability="create_record",
                    args={"entity": "process", "data": {"nome": "X"}},
                )
        with patch.object(
            orch._dispatch, "create_record", return_value=(created, "ok", 201)
        ):
            with patch.object(orch._dispatch, "get_record", return_value=created):
                first = orch.act(
                    request,
                    capability="create_record",
                    proposal_handle=prepared["proposal_handle"],
                )
        assert first["verified"] is True
        with pytest.raises(GovernedWriteError) as exc:
            orch.act(
                request,
                capability="create_record",
                proposal_handle=prepared["proposal_handle"],
            )
        assert exc.value.code in {PROPOSAL_STALE, "proposal_not_found"}

    def test_package_incomplete_no_act(self):
        orch = GovernedWriteOrchestrator()
        request = _request_for(_auth_user())
        with patch.object(
            orch._packages,
            "validate",
            return_value={"ready": False, "missing": ["process.nome"]},
        ):
            with patch(
                "tm_app.interface.http.branch_access_http.require_transformometro_view_access",
                return_value=None,
            ):
                prepared = orch.prepare(
                    request,
                    capability="commit_improvement_package",
                    args={"process": {}, "instance": {}},
                )
        assert prepared["act_allowed"] is False
        assert prepared["ready"] is False
        with pytest.raises(GovernedWriteError):
            orch.act(
                request,
                capability="commit_improvement_package",
                proposal_handle=prepared["proposal_handle"],
            )


class TestDispatchAuthZ:
    def test_activate_revision_unauthorized(self):
        dispatch = GptActionsDispatchService()
        request = _request_for(_auth_user(permissions=["transformometro.view"]))
        with patch(
            "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
        ) as repo_cls:
            repo_cls.return_value.get.return_value = {
                "revisao_id": "r1",
                "processo_id": "p1",
                "instancia_id": "",
            }
            with patch(
                "tm_app.application.gpt_actions.dispatch_service.check_processo_manage_access",
                return_value=MagicMock(status_code=403),
            ):
                with pytest.raises(GptActionsError) as exc:
                    dispatch.activate_revision(request, "r1")
        assert exc.value.status_code == 403

    def test_recalculate_dashboard_unauthorized(self):
        dispatch = GptActionsDispatchService()
        request = _request_for(_auth_user(permissions=[]))
        with pytest.raises(GptActionsError) as exc:
            dispatch.recalculate_dashboard(request)
        assert exc.value.status_code == 403


class TestMcpBridgeGoverned:
    def _auth(self, **kwargs):
        user_token = set_current_user(_auth_user(**kwargs))
        auth_token = set_request_authorization("Bearer test")
        return user_token, auth_token

    def test_validate_package_prepare_alias(self):
        user_token, auth_token = self._auth()
        try:
            with patch(
                "tm_app.interface.mcp.tool_bridge._orchestrator.prepare",
                return_value={
                    "proposal_handle": "h",
                    "ready": False,
                    "act_allowed": False,
                    "validation_result": {"ready": False, "missing": ["x"]},
                },
            ):
                result = tool_validate_improvement_package(process={}, instance={})
            assert result.isError is False
            assert result.structuredContent["data"]["ready"] is False
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_commit_without_handle_errors(self):
        user_token, auth_token = self._auth()
        try:
            result = tool_commit_improvement_package(
                process={"nome": "X"},
                instance={"filial_id": "filial-01"},
                dry_run=False,
            )
            assert result.isError is True
            assert (
                result.structuredContent["data"]["error_code"] == "proposal_required"
            )
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_manage_evidence_delete_without_confirm_prepare_error(self):
        user_token, auth_token = self._auth()
        try:
            result = tool_manage_evidence(
                scope="process",
                operation="delete",
                parent_id="p1",
                evidence_id="e1",
                confirm_delete=False,
            )
            assert result.isError is True
            assert "confirm_delete" in result.structuredContent["message"]
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_act_create_verified_false_is_error(self):
        user_token, auth_token = self._auth()
        try:
            with patch(
                "tm_app.interface.mcp.tool_bridge._orchestrator.act",
                return_value={"verified": False, "data": {}},
            ):
                result = tool_act_create_record("fake.handle")
            assert result.isError is True
            assert (
                result.structuredContent["data"]["error_code"]
                == OUTCOME_VERIFICATION_FAILED
            )
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_get_catalog_unauthorized_without_user(self):
        result = tool_get_catalog()
        assert result.isError is True
        assert result.structuredContent["status_code"] == 401

    def test_prepare_recalculate_forbidden_via_bridge(self):
        user_token, auth_token = self._auth(permissions=[])
        try:
            result = tool_prepare_recalculate_dashboard()
            assert result.isError is True
            assert result.structuredContent["status_code"] == 403
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)

    def test_prepare_activate_forbidden_via_bridge(self):
        user_token, auth_token = self._auth(permissions=["transformometro.view"])
        try:
            with patch(
                "tm_app.application.gpt_actions.dispatch_service.RevisaoRepository"
            ) as repo_cls:
                repo_cls.return_value.get.return_value = {
                    "revisao_id": "r1",
                    "processo_id": "p1",
                    "instancia_id": "",
                }
                with patch(
                    "tm_app.application.gpt_actions.dispatch_service.check_processo_manage_access",
                    return_value=MagicMock(status_code=403),
                ):
                    with patch(
                        "tm_app.interface.mcp.tool_bridge._orchestrator._dispatch.get_record",
                        return_value={"id": "r1"},
                    ):
                        result = tool_prepare_activate_revision("r1")
            assert result.isError is True
            assert result.structuredContent["status_code"] == 403
        finally:
            reset_request_authorization(auth_token)
            reset_current_user(user_token)
