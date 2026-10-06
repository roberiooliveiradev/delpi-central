"""TÉO MCP — Diagnostic V1 controlled surface tests (Prompt 8).

Covers exactly four new MCP-native tools:
  get_diagnostic / list_diagnostics_by_revision (READ)
  prepare_create_diagnostic / prepare_manage_diagnostic (PREPARE)
commit_proposal remains the only ACT. No GPT Action surface is added.
"""

from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from starlette.requests import Request

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.application.gpt_actions.governed_actions_facade import (
    GovernedActionsFacade,
)
from tm_app.application.governed_writes.diagnostic_capabilities import (
    MANAGE_ACTIONS,
    DiagnosticWriteStack,
)
from tm_app.application.governed_writes.orchestrator import (
    GovernedWriteOrchestrator,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.application.ports.evidence_reader_port import EvidenceRef
from tm_app.application.ports.revision_reader_port import RevisionContext
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
)
from tm_app.application.use_cases.diagnostic_write import DiagnosticWriteUseCase
from tm_app.domain.diagnostic.diagnostic import (
    CausalLink,
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    EffectiveValidation,
    EpistemicState,
    EvidenceLink,
    EvidenceRelation,
    Finding,
    Hypothesis,
    ProblemStatement,
    RootCauseDesignation,
)
from tm_app.infrastructure.security.diagnostic_authorization import (
    FreshAuthorizationAdapter,
)
from tm_app.application.gpt_actions.openapi_builder import (
    GPT_ACTIONS_OPERATION_IDS,
)
from tm_app.interface.mcp.constants import (
    GPT_TO_MCP_TOOLS,
    MCP_NATIVE_TOOLS,
    MCP_TOOL_NAMES,
    PREPARE_TOOL_CAPABILITY,
    TOOL_CLASS,
)
from tm_app.interface.mcp.server import create_mcp_server
from tm_app.interface.mcp import tool_bridge as bridge

USER_ID = str(uuid4())
REV_A = str(uuid4())
EV_IN = str(uuid4())
EV_OUT = str(uuid4())


def _user(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=USER_ID,
        email="teo@delpi",
        name="Téo",
        is_superadmin=False,
        permissions=[ACCESS_PERMISSION],
        principal_type="user",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _prime_ctx(user=None):
    set_current_user(user or _user())
    set_request_authorization("Bearer test-token")


@pytest.fixture(autouse=True)
def _clean_state():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()
    clear_current_user()
    clear_request_authorization()


# ---------------------------------------------------------------------------
# Fakes — same shape as governed-write tests
# ---------------------------------------------------------------------------


class FakeDiagnosticRepo:
    def __init__(self) -> None:
        self._store: dict[str, Diagnostic] = {}
        self.save = MagicMock(side_effect=self._save)
        self.create = MagicMock(side_effect=self._create)

    def _create(self, diagnostic: Diagnostic) -> Diagnostic:
        self._store[diagnostic.diagnostic_id] = diagnostic
        return diagnostic

    def _save(self, diagnostic: Diagnostic, *, expected_version: int) -> int:
        if diagnostic.version != expected_version:
            raise RuntimeError("version drift in fake")
        object.__setattr__(diagnostic, "_version", diagnostic.version + 1)
        return diagnostic.version

    def seed(self, diagnostic: Diagnostic) -> None:
        self._store[diagnostic.diagnostic_id] = diagnostic

    def get(self, diagnostic_id):
        return self._store.get(diagnostic_id)

    def list_by_revision(self, revision_id):
        return sorted(
            (d for d in self._store.values() if d.revision_id == revision_id),
            key=lambda d: d.diagnostic_id,
        )


class FakeRevisionReader:
    def __init__(self) -> None:
        self._ctx = RevisionContext(
            revision_id=REV_A,
            processo_id=str(uuid4()),
            instancia_id=str(uuid4()),
            versao_revisao="v1",
            cenario_tipo="as_is",
            revisao_referencia_id=None,
        )

    def get(self, revision_id):
        if revision_id == REV_A:
            return self._ctx
        return None


class FakeEvidenceReader:
    """EV_IN resolves inside REV_A; EV_OUT is outside → unresolved."""

    def list_by_revision(self, revision_id):
        if revision_id == REV_A:
            return [EvidenceRef(EV_IN, REV_A, "anexo", "e.pdf", None)]
        return []


class FakeCoreRbac:
    def __init__(self) -> None:
        self.permissions = [ACCESS_PERMISSION]
        self.fail = False
        self.calls: list[bool] = []

    async def __call__(self, token, *, force_refresh=False):
        self.calls.append(force_refresh)
        if self.fail:
            raise RuntimeError("Core down")
        return {
            "id": USER_ID,
            "email": "teo@delpi",
            "permissions": list(self.permissions),
            "is_superadmin": False,
        }


@pytest.fixture()
def rbac(monkeypatch):
    fake = FakeCoreRbac()
    monkeypatch.setattr(
        "tm_app.infrastructure.security.diagnostic_authorization.load_user_rbac",
        fake,
    )
    yield fake


@pytest.fixture()
def repo() -> FakeDiagnosticRepo:
    return FakeDiagnosticRepo()


@pytest.fixture()
def stack(repo) -> DiagnosticWriteStack:
    return DiagnosticWriteStack(
        use_case=DiagnosticWriteUseCase(
            diagnostics=repo,
            revisions=FakeRevisionReader(),
            evidence=FakeEvidenceReader(),
            authorization=FreshAuthorizationAdapter(),
        ),
        diagnostics=repo,
        revisions=FakeRevisionReader(),
        evidence=FakeEvidenceReader(),
    )


@pytest.fixture()
def governed(stack, monkeypatch):
    """Bridge sees the REAL facade+orchestrator wired to fake infra."""
    orch = GovernedWriteOrchestrator(diagnostic_stack=stack)
    facade = GovernedActionsFacade(orchestrator=orch)
    monkeypatch.setattr(bridge, "_governed", facade)
    monkeypatch.setattr(bridge, "_diagnostic_stack", stack)
    return facade


def _structured(result) -> dict:
    assert result.structured_content is not None
    return result.structured_content


def _seed_diagnostic(repo, **kwargs) -> Diagnostic:
    kwargs.setdefault("problem_statement", ProblemStatement("problema real"))
    diagnostic = Diagnostic(
        diagnostic_id=str(uuid4()), revision_id=REV_A, **kwargs
    )
    repo.seed(diagnostic)
    return diagnostic


# ---------------------------------------------------------------------------
# SURFACE / REGISTRATION
# ---------------------------------------------------------------------------


class TestSurfaceRegistration:
    def test_exactly_four_new_tools_registered(self):
        tools = asyncio.run(create_mcp_server().list_tools())
        names = {t.name for t in tools}
        assert {
            "get_diagnostic",
            "list_diagnostics_by_revision",
            "prepare_create_diagnostic",
            "prepare_manage_diagnostic",
        } <= names

    def test_tool_classes_correct(self):
        assert TOOL_CLASS["get_diagnostic"] == "READ"
        assert TOOL_CLASS["list_diagnostics_by_revision"] == "READ"
        assert TOOL_CLASS["prepare_create_diagnostic"] == "PREPARE"
        assert TOOL_CLASS["prepare_manage_diagnostic"] == "PREPARE"

    def test_mcp_native_flagged_no_gpt_parity(self):
        assert MCP_NATIVE_TOOLS == {
            "get_diagnostic",
            "list_diagnostics_by_revision",
            "prepare_create_diagnostic",
            "prepare_manage_diagnostic",
        }

    def test_commit_proposal_is_the_only_act(self):
        act_tools = [n for n, c in TOOL_CLASS.items() if c == "ACT"]
        assert act_tools == ["commit_proposal"]

    def test_no_diagnostic_act_or_generic_executor(self):
        forbidden = {
            "act_diagnostic",
            "commit_diagnostic",
            "execute_diagnostic",
            "diagnostic_write",
        }
        assert forbidden.isdisjoint(MCP_TOOL_NAMES)
        assert forbidden.isdisjoint(set(GPT_ACTIONS_OPERATION_IDS))

    def test_no_new_gpt_operation_ids(self):
        blob = json.dumps(sorted(GPT_ACTIONS_OPERATION_IDS))
        assert "diagnostic" not in blob
        for tools in GPT_TO_MCP_TOOLS.values():
            assert not any("diagnostic" in t for t in tools)

    def test_prepare_capability_mapping(self):
        assert (
            PREPARE_TOOL_CAPABILITY["prepare_create_diagnostic"]
            == "create_diagnostic"
        )
        assert (
            PREPARE_TOOL_CAPABILITY["prepare_manage_diagnostic"]
            == "manage_diagnostic"
        )

    def test_annotations_read_vs_prepare(self):
        tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
        assert tools["get_diagnostic"].annotations.read_only_hint is True
        assert tools["list_diagnostics_by_revision"].annotations.read_only_hint is True
        assert tools["prepare_create_diagnostic"].annotations.read_only_hint is False
        assert tools["prepare_manage_diagnostic"].annotations.read_only_hint is False
        assert tools["prepare_manage_diagnostic"].annotations.destructive_hint is False

    def test_create_schema_never_requests_diagnostic_id(self):
        tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
        props = tools["prepare_create_diagnostic"].input_schema["properties"]
        assert "diagnostic_id" not in props
        assert "commit_now" not in props
        assert set(props) == {"revision_id", "problem_statement", "provenance"}

    def test_manage_schema_action_is_closed_allowlist_of_13(self):
        tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
        action_schema = tools["prepare_manage_diagnostic"].input_schema[
            "properties"
        ]["action"]
        assert set(action_schema["enum"]) == set(MANAGE_ACTIONS)
        assert len(action_schema["enum"]) == 13
        # commit_now must not leak into the public schema
        props = tools["prepare_manage_diagnostic"].input_schema["properties"]
        assert "commit_now" not in props


# ---------------------------------------------------------------------------
# READ — get_diagnostic
# ---------------------------------------------------------------------------


class TestGetDiagnostic:
    def test_success_projects_context(self, governed, repo, rbac):
        _prime_ctx()
        hyp = Hypothesis(hypothesis_id=str(uuid4()), statement="causa?")
        finding = Finding(finding_id=str(uuid4()), statement="observado")
        diagnostic = _seed_diagnostic(
            repo,
            findings=(finding,),
            hypotheses=(hyp,),
            evidence_links=(
                EvidenceLink(
                    link_id=str(uuid4()),
                    evidence_id=EV_IN,
                    relation=EvidenceRelation.SUPPORTS,
                    target_id=None,
                ),
                EvidenceLink(
                    link_id=str(uuid4()),
                    evidence_id=EV_OUT,  # foreign → unresolved
                    relation=EvidenceRelation.SUPPORTS,
                    target_id=None,
                ),
            ),
        )
        result = bridge.tool_get_diagnostic(diagnostic.diagnostic_id)
        data = _structured(result)["data"]
        assert data["diagnostic"]["diagnostic_id"] == diagnostic.diagnostic_id
        assert data["diagnostic"]["problem_statement"] == "problema real"
        assert data["revision"]["revision_id"] == REV_A
        # epistemic semantics preserved
        assert data["diagnostic"]["findings"][0]["epistemic_state"] == "OBSERVED"
        assert (
            data["diagnostic"]["hypotheses"][0]["epistemic_state"] == "INFERRED"
        )
        # evidence: one resolved, one unresolved — never silently dropped
        links = data["evidence_links"]
        assert len(links) == 2
        resolved = [l for l in links if l["resolved_in_revision"]]
        unresolved = [l for l in links if not l["resolved_in_revision"]]
        assert resolved[0]["evidence"]["evidence_id"] == EV_IN
        assert unresolved[0]["evidence"] is None
        assert unresolved[0]["evidence_id"] == EV_OUT
        assert (
            unresolved[0]["link_id"]
            in data["data_quality"]["unresolved_evidence_links"]
        )
        assert isinstance(data["data_quality"]["signals"], list)

    def test_read_does_not_write(self, governed, repo, rbac):
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        bridge.tool_get_diagnostic(diagnostic.diagnostic_id)
        repo.save.assert_not_called()
        repo.create.assert_not_called()

    def test_missing_auth_returns_401(self, governed):
        result = bridge.tool_get_diagnostic(str(uuid4()))
        data = _structured(result)
        assert data["success"] is False
        assert data["status_code"] == 401
        assert data["data"]["error_code"] == "unauthenticated"

    def test_service_principal_denied_403(self, governed):
        _prime_ctx(_user(principal_type="service"))
        result = bridge.tool_get_diagnostic(str(uuid4()))
        assert _structured(result)["status_code"] == 403

    def test_missing_access_returns_403(self, governed):
        _prime_ctx(_user(permissions=[]))
        result = bridge.tool_get_diagnostic(str(uuid4()))
        assert _structured(result)["status_code"] == 403

    def test_missing_diagnostic_returns_404(self, governed, repo):
        _prime_ctx()
        result = bridge.tool_get_diagnostic(str(uuid4()))
        data = _structured(result)
        assert data["status_code"] == 404
        assert data["data"]["error_kind"] == "not_found"
        assert data["data"]["error_code"] == "diagnostic.not_found"

    def test_no_security_internals_in_output(self, governed, repo, rbac):
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        blob = json.dumps(
            bridge.tool_get_diagnostic(diagnostic.diagnostic_id).structured_content
        )
        for forbidden in (
            "access_token",
            "Authorization",
            "permissions",
            "roles",
            "groups",
            "is_superadmin",
            "principal_type",
            "test-token",
        ):
            assert forbidden not in blob


# ---------------------------------------------------------------------------
# READ — list_diagnostics_by_revision
# ---------------------------------------------------------------------------


class TestListDiagnosticsByRevision:
    def test_success_canonical_ordering_no_fanout(self, governed, repo, rbac):
        _prime_ctx()
        d_b = _seed_diagnostic(repo)
        d_a = _seed_diagnostic(repo)
        # canonical ordering = diagnostic_id ASC
        ordered = sorted([d_a.diagnostic_id, d_b.diagnostic_id])
        result = bridge.tool_list_diagnostics_by_revision(REV_A)
        data = _structured(result)["data"]
        assert data["revision"]["revision_id"] == REV_A
        assert [i["diagnostic_id"] for i in data["items"]] == ordered
        # summaries only — no evidence fan-out
        for item in data["items"]:
            assert "evidence_links" not in item
            assert "evidence_links_count" in item

    def test_missing_revision_returns_404(self, governed):
        _prime_ctx()
        result = bridge.tool_list_diagnostics_by_revision(str(uuid4()))
        assert _structured(result)["status_code"] == 404

    def test_missing_auth_returns_401(self, governed):
        result = bridge.tool_list_diagnostics_by_revision(REV_A)
        assert _structured(result)["status_code"] == 401

    def test_service_principal_denied(self, governed):
        _prime_ctx(_user(principal_type="service"))
        result = bridge.tool_list_diagnostics_by_revision(REV_A)
        assert _structured(result)["status_code"] == 403


# ---------------------------------------------------------------------------
# PREPARE — create
# ---------------------------------------------------------------------------


class TestPrepareCreateDiagnostic:
    def test_prepare_returns_proposal_with_generated_uuid(
        self, governed, repo, rbac
    ):
        _prime_ctx()
        result = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A,
            problem_statement="gargalo no setup",
        )
        data = _structured(result)["data"]
        handle = data["proposal"]["handle"]
        exact = data["proposal"]["exact_change"]
        generated = exact["diagnostic_id"]
        # valid UUID, server-side (caller had no chance to supply it)
        from uuid import UUID

        assert UUID(generated)  # parses
        assert exact["revision_id"] == REV_A
        assert data["proposal"]["act_allowed"] is True
        # no persistence at PREPARE
        repo.create.assert_not_called()
        repo.save.assert_not_called()
        assert handle

    def test_prepare_rejects_unknown_revision(self, governed, rbac):
        _prime_ctx()
        result = bridge.tool_prepare_create_diagnostic(
            revision_id=str(uuid4()),
            problem_statement="x",
        )
        data = _structured(result)
        assert data["success"] is False
        assert data["status_code"] in (400, 404)

    def test_prepare_requires_user_principal(self, governed, rbac):
        _prime_ctx(_user(principal_type="service"))
        result = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A, problem_statement="x"
        )
        assert _structured(result)["status_code"] == 403

    def test_prepare_requires_access_permission(self, governed, rbac):
        _prime_ctx(_user(permissions=[]))
        result = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A, problem_statement="x"
        )
        assert _structured(result)["status_code"] == 403


# ---------------------------------------------------------------------------
# PREPARE — manage (13 actions, generated ids, reference ids preserved)
# ---------------------------------------------------------------------------


class TestPrepareManageDiagnostic:
    ADDITIVE_ID_FIELD = {
        "add_finding": "finding_id",
        "add_hypothesis": "hypothesis_id",
        "add_causal_link": "link_id",
        "add_evidence_link": "link_id",
        "add_conclusion": "conclusion_id",
    }

    PAYLOADS = {
        "add_finding": {"statement": "obs"},
        "add_hypothesis": {"statement": "hip"},
        "add_causal_link": {
            "source_hypothesis_id": "h-src",
            "target_id": "h-tgt",
        },
        "add_evidence_link": {"evidence_id": EV_IN, "relation": "SUPPORTS"},
        "add_conclusion": {"statement": "concl"},
    }

    def test_unknown_action_rejected(self, governed, repo):
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        result = bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action="delete_diagnostic",
            payload={},
        )
        data = _structured(result)
        assert data["success"] is False
        assert data["status_code"] == 400

    @pytest.mark.parametrize("action", sorted(ADDITIVE_ID_FIELD))
    def test_additive_generates_id_server_side(
        self, governed, repo, rbac, action
    ):
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        # seed a hypothesis so causal/conclusion references resolve
        if action in ("add_causal_link",):
            pass  # references may be unresolved; PREPARE still forms proposal
        payload = dict(self.PAYLOADS[action])
        result = bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action=action,
            payload=payload,
        )
        data = _structured(result)["data"]
        exact = data["proposal"]["exact_change"]["payload"]
        id_field = self.ADDITIVE_ID_FIELD[action]
        from uuid import UUID

        assert UUID(exact[id_field])  # generated, valid
        # referenced ids preserved exactly
        for key, value in self.PAYLOADS[action].items():
            assert exact[key] == value

    @pytest.mark.parametrize("action", sorted(ADDITIVE_ID_FIELD))
    def test_caller_supplied_creation_id_rejected(
        self, governed, repo, action
    ):
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        payload = dict(self.PAYLOADS[action])
        payload[self.ADDITIVE_ID_FIELD[action]] = "caller-chosen-id"
        result = bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action=action,
            payload=payload,
        )
        data = _structured(result)
        assert data["success"] is False
        assert data["status_code"] == 400
        assert "server-generated" in data["message"]

    def test_lifecycle_action_preserves_existing_target_id(
        self, governed, repo, rbac
    ):
        _prime_ctx()
        hyp = Hypothesis(hypothesis_id=str(uuid4()), statement="h")
        diagnostic = _seed_diagnostic(repo, hypotheses=(hyp,))
        result = bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action="validate_hypothesis",
            payload={"hypothesis_id": hyp.hypothesis_id},
        )
        data = _structured(result)["data"]
        exact = data["proposal"]["exact_change"]["payload"]
        assert exact["hypothesis_id"] == hyp.hypothesis_id
        # no injected replacement field
        assert "link_id" not in exact
        assert "finding_id" not in exact

    def test_prepare_persists_nothing(self, governed, repo, rbac):
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action="add_finding",
            payload={"statement": "x"},
        )
        repo.save.assert_not_called()
        assert repo.get(diagnostic.diagnostic_id).version == 1

    def test_evidence_outside_revision_not_act_allowed(
        self, governed, repo, rbac
    ):
        """Foreign-revision evidence → proposal not ready, never ACT."""
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        result = bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action="add_evidence_link",
            payload={"evidence_id": EV_OUT, "relation": "SUPPORTS"},
        )
        data = _structured(result)["data"]
        proposal = data["proposal"]
        # governed contract: blocked at PREPARE (validation error or
        # act_allowed=false) — must never reach ACT successfully.
        ready = proposal.get("act_allowed", True) and data.get(
            "validation_result", {}
        ).get("ready", True)
        assert ready is False or _structured(result)["success"] is False


# ---------------------------------------------------------------------------
# COMMON COMMIT — end-to-end through bridge → facade → orchestrator
# ---------------------------------------------------------------------------


class TestCommonCommit:
    def test_commit_auto_act_no_extra_confirmation_and_fresh_authz(
        self, governed, repo, rbac
    ):
        """create_diagnostic is execution_policy=auto_act: the user request
        is the intent — commit_proposal(confirmation=False) must execute,
        still with fresh AuthZ + authoritative read-back + verify."""
        _prime_ctx()
        prepared = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A, problem_statement="fluxo real"
        )
        proposal = _structured(prepared)["data"]["proposal"]
        assert proposal.get("execution_policy") == "auto_act"
        handle = proposal["handle"]

        committed = bridge.tool_commit_proposal(handle, confirmation=False)
        data = _structured(committed)
        assert data["success"] is True
        # fresh Core AuthZ ran at ACT
        assert rbac.calls and rbac.calls[-1] is True
        # canonical use case wrote + read-back verified
        repo.create.assert_called_once()
        assert data["data"]["postcondition"]["verified"] is True
        assert data["data"]["persisted"] is True

    def test_commit_confirm_before_act_requires_confirmation(
        self, governed, repo, rbac
    ):
        """manage_diagnostic is execution_policy=confirm_before_act:
        commit_proposal(confirmation=False) must be rejected; explicit
        confirmation then executes normally."""
        _prime_ctx()
        diagnostic = _seed_diagnostic(repo)
        prepared = bridge.tool_prepare_manage_diagnostic(
            diagnostic_id=diagnostic.diagnostic_id,
            action="add_finding",
            payload={"statement": "obs"},
        )
        proposal = _structured(prepared)["data"]["proposal"]
        assert proposal.get("execution_policy") == "confirm_before_act"
        handle = proposal["handle"]

        denied = bridge.tool_commit_proposal(handle, confirmation=False)
        assert _structured(denied)["success"] is False

        committed = bridge.tool_commit_proposal(handle, confirmation=True)
        assert _structured(committed)["success"] is True

    def test_revoke_between_prepare_and_commit_denied(
        self, governed, repo, rbac
    ):
        _prime_ctx()
        prepared = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A, problem_statement="x"
        )
        handle = _structured(prepared)["data"]["proposal"]["handle"]
        rbac.permissions = []  # Core revoked transformometro.access
        committed = bridge.tool_commit_proposal(handle, confirmation=True)
        assert _structured(committed)["success"] is False
        repo.create.assert_not_called()

    def test_commit_wrong_actor_rejected(self, governed, repo, rbac):
        _prime_ctx(_user(id="actor-a"))
        prepared = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A, problem_statement="x"
        )
        handle = _structured(prepared)["data"]["proposal"]["handle"]
        _prime_ctx(_user(id="actor-b"))  # different actor at commit
        committed = bridge.tool_commit_proposal(handle, confirmation=True)
        assert _structured(committed)["success"] is False
        repo.create.assert_not_called()

    def test_commit_is_single_use(self, governed, repo, rbac):
        _prime_ctx()
        prepared = bridge.tool_prepare_create_diagnostic(
            revision_id=REV_A, problem_statement="x"
        )
        handle = _structured(prepared)["data"]["proposal"]["handle"]
        first = bridge.tool_commit_proposal(handle, confirmation=True)
        assert _structured(first)["success"] is True
        replay = bridge.tool_commit_proposal(handle, confirmation=True)
        assert _structured(replay)["success"] is False
        assert repo.create.call_count == 1

    def test_commit_only_accepts_proposal_handle(self):
        tools = {t.name: t for t in asyncio.run(create_mcp_server().list_tools())}
        props = tools["commit_proposal"].input_schema["properties"]
        assert "capability" not in props
        assert "action" not in props
        assert set(props) <= {"proposal_handle", "confirmation"}
