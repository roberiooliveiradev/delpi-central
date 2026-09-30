"""Diagnostic Portal HTTP surface — route-level tests.

Exercises the real route functions with the canonical governed stack
(wired over fake ports). The real ``FreshAuthorizationAdapter`` runs at
ACT with a monkeypatched Core lookup, so the same fresh, fail-closed
AuthZ path as runtime is covered — including service-principal denial
and Core-unavailable 503.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from pydantic import ValidationError
from starlette.requests import Request

from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)

import tm_app.interface.http.routes.diagnostic_routes as routes
from tm_app.application.governed_writes.diagnostic_capabilities import (
    MANAGE_ACTIONS,
    DiagnosticWriteStack,
)
from tm_app.application.governed_writes.orchestrator import (
    GovernedWriteOrchestrator,
)
from tm_app.application.gpt_actions.governed_actions_facade import (
    GovernedActionsFacade,
)
from tm_app.application.governed_writes.proposal_store import (
    reset_proposal_store_for_tests,
)
from tm_app.application.ports.evidence_reader_port import EvidenceRef
from tm_app.application.ports.revision_reader_port import RevisionContext
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
)
from tm_app.application.services.transformometro_realtime_notify import (
    infer_section_key,
    _related_rooms,
)
from tm_app.application.use_cases.diagnostic_write import DiagnosticWriteUseCase
from tm_app.domain.diagnostic.diagnostic import (
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    EffectiveValidation,
    Hypothesis,
    ProblemStatement,
    RootCauseDesignation,
)
from tm_app.infrastructure.security.diagnostic_authorization import (
    FreshAuthorizationAdapter,
)

REV_A = str(uuid4())
EV1 = str(uuid4())
USER_ID = "u-portal-1"
OTHER_USER_ID = "u-portal-2"


# ---------------------------------------------------------------------------
# Fakes — ports only; the authorization adapter is the REAL one.
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
        return [
            d for d in self._store.values() if d.revision_id == revision_id
        ]


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
    def list_by_revision(self, revision_id):
        if revision_id == REV_A:
            return [EvidenceRef(EV1, REV_A, "anexo", "e.pdf", None)]
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
            "email": "u@delpi",
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
    clear_current_user()
    clear_request_authorization()


@pytest.fixture(autouse=True)
def _clean_store():
    reset_proposal_store_for_tests()
    yield
    reset_proposal_store_for_tests()


def _user(**kwargs) -> SimpleNamespace:
    defaults = dict(
        id=USER_ID,
        email="u@delpi",
        name="Portal User",
        is_superadmin=False,
        permissions=[ACCESS_PERMISSION],
        principal_type="user",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _request(user=None, *, client_id: str | None = None) -> Request:
    headers = []
    if client_id:
        headers.append(
            (b"x-transformometro-client-id", client_id.encode("utf-8"))
        )
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/portal",
        "raw_path": b"/portal",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 0),
        "server": ("transformometro-api", 443),
    }
    request = Request(scope)
    request.state.user = user if user is not None else _user()
    return request


def _stack(repo: FakeDiagnosticRepo) -> DiagnosticWriteStack:
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
def wired(monkeypatch):
    """Wire the route module to fake ports; canonical logic stays real."""
    repo = FakeDiagnosticRepo()
    stack = _stack(repo)
    orch = GovernedWriteOrchestrator(diagnostic_stack=stack)
    monkeypatch.setattr(routes, "_diagnostic_stack", stack)
    monkeypatch.setattr(routes, "_orchestrator", orch)
    monkeypatch.setattr(routes, "_governed", GovernedActionsFacade(orch))
    yield repo


@pytest.fixture()
def notified(monkeypatch):
    calls = []
    monkeypatch.setattr(
        routes, "notify_entity_updated", lambda **kw: calls.append(kw)
    )
    return calls


def _diagnostic(**kwargs) -> Diagnostic:
    kwargs.setdefault("diagnostic_id", str(uuid4()))
    kwargs.setdefault("revision_id", REV_A)
    kwargs.setdefault("problem_statement", ProblemStatement("problema"))
    return Diagnostic(**kwargs)


def _prime_act_ctx(user=None):
    set_current_user(user or _user())
    set_request_authorization("Bearer tok")


def _body(resp):
    return json.loads(resp.body)


# ---------------------------------------------------------------------------
# READ ROUTES
# ---------------------------------------------------------------------------


def test_list_route_delegates_to_canonical_read(wired):
    repo = wired
    diag = _diagnostic()
    repo.seed(diag)
    resp = routes.list_diagnostics(_request(), REV_A)
    assert resp.status_code == 200
    data = _body(resp)["data"]
    assert data["total"] == 1
    assert data["items"][0]["diagnostic_id"] == diag.diagnostic_id
    assert data["items"][0]["problem_statement"] == "problema"
    assert data["revision"]["revision_id"] == REV_A


def test_list_route_unknown_revision_is_404(wired):
    resp = routes.list_diagnostics(_request(), str(uuid4()))
    assert resp.status_code == 404
    assert _body(resp)["data"]["error_code"] == "diagnostic.revision_not_found"


def test_get_route_delegates_to_canonical_read(wired):
    diag = _diagnostic()
    wired.seed(diag)
    resp = routes.get_diagnostic(_request(), diag.diagnostic_id)
    assert resp.status_code == 200
    data = _body(resp)["data"]
    assert data["diagnostic"]["diagnostic_id"] == diag.diagnostic_id
    assert data["diagnostic"]["revision_id"] == REV_A
    assert data["revision"]["revision_id"] == REV_A
    assert "data_quality" in data


def test_get_route_not_found_is_404(wired):
    resp = routes.get_diagnostic(_request(), str(uuid4()))
    assert resp.status_code == 404
    assert _body(resp)["data"]["error_code"] == "diagnostic.not_found"


def test_read_routes_require_authentication(wired):
    request = _request()
    request.state.user = None
    assert routes.list_diagnostics(request, REV_A).status_code == 401
    assert routes.get_diagnostic(request, str(uuid4())).status_code == 401


def test_read_routes_deny_service_principal(wired):
    request = _request(_user(principal_type="service"))
    assert routes.list_diagnostics(request, REV_A).status_code == 403
    assert routes.get_diagnostic(request, str(uuid4())).status_code == 403


def test_read_routes_deny_missing_access_permission(wired):
    request = _request(_user(permissions=[]))
    assert routes.list_diagnostics(request, REV_A).status_code == 403
    assert routes.get_diagnostic(request, str(uuid4())).status_code == 403


# ---------------------------------------------------------------------------
# PREPARE — CREATE
# ---------------------------------------------------------------------------


def test_prepare_create_seals_server_generated_id_and_user_provenance(
    wired, notified
):
    repo = wired
    resp = routes.prepare_create_diagnostic(
        _request(),
        REV_A,
        routes.DiagnosticCreatePrepareBody(problem_statement="raiz"),
    )
    assert resp.status_code == 200
    proposal = _body(resp)["data"]
    assert proposal["proposal_handle"]
    assert proposal["act_allowed"] is True
    change = proposal["exact_change"]
    assert change["action"] == "create"
    assert change["revision_id"] == REV_A
    uuid4_check = change["diagnostic_id"]
    assert uuid4_check and "-" in uuid4_check  # uuid4 hex form
    assert change["provenance"]["origin"] == "USER"
    # PREPARE writes nothing
    assert repo.create.call_count == 0
    assert repo.save.call_count == 0
    assert repo.get(uuid4_check) is None
    # PREPARE never emits realtime
    assert notified == []


def test_prepare_create_rejects_caller_technical_id():
    with pytest.raises(ValidationError):
        routes.DiagnosticCreatePrepareBody(
            problem_statement="x",
            diagnostic_id="caller-picked",
        )


def test_prepare_create_unknown_revision_is_404(wired):
    resp = routes.prepare_create_diagnostic(
        _request(),
        str(uuid4()),
        routes.DiagnosticCreatePrepareBody(problem_statement="x"),
    )
    assert resp.status_code == 404


def test_prepare_create_denies_service_principal(wired):
    resp = routes.prepare_create_diagnostic(
        _request(_user(principal_type="service")),
        REV_A,
        routes.DiagnosticCreatePrepareBody(problem_statement="x"),
    )
    assert resp.status_code == 403


def test_prepare_create_requires_authentication(wired):
    request = _request()
    request.state.user = None
    resp = routes.prepare_create_diagnostic(
        request,
        REV_A,
        routes.DiagnosticCreatePrepareBody(problem_statement="x"),
    )
    assert resp.status_code == 401


def test_prepare_create_denies_missing_access_permission(wired):
    resp = routes.prepare_create_diagnostic(
        _request(_user(permissions=[])),
        REV_A,
        routes.DiagnosticCreatePrepareBody(problem_statement="x"),
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# PREPARE — MANAGE (closed action list + server ids + provenance)
# ---------------------------------------------------------------------------


def _seeded(repo: FakeDiagnosticRepo) -> Diagnostic:
    diag = _diagnostic()
    repo.seed(diag)
    return diag


def test_prepare_manage_seals_server_generated_finding_id(wired, notified):
    diag = _seeded(wired)
    resp = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_finding", payload={"statement": "sintoma"}
        ),
    )
    assert resp.status_code == 200
    payload = _body(resp)["data"]["exact_change"]["payload"]
    assert payload["finding_id"]  # server-generated
    assert payload["provenance"]["origin"] == "USER"
    assert wired.save.call_count == 0
    assert notified == []


def test_prepare_manage_rejects_caller_technical_id(wired):
    diag = _seeded(wired)
    resp = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_finding",
            payload={"finding_id": "caller-picked", "statement": "x"},
        ),
    )
    assert resp.status_code == 422
    assert _body(resp)["data"]["error_code"] == "server_owned_field"


def test_prepare_manage_rejects_unsupported_action(wired):
    diag = _seeded(wired)
    resp = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="drop_database", payload={}
        ),
    )
    assert resp.status_code == 422
    assert _body(resp)["data"]["error_code"] == "unsupported_action"


def test_prepare_manage_rejects_teo_provenance_claim(wired):
    diag = _seeded(wired)
    resp = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_finding",
            payload={
                "statement": "x",
                "provenance": {"origin": "TEO"},
            },
        ),
    )
    assert resp.status_code == 422


def test_prepare_manage_preserves_user_provenance_detail(wired):
    diag = _seeded(wired)
    resp = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_hypothesis",
            payload={
                "statement": "causa",
                "provenance": {"origin": "USER", "detail": "observado"},
            },
        ),
    )
    assert resp.status_code == 200
    payload = _body(resp)["data"]["exact_change"]["payload"]
    assert payload["provenance"] == {"origin": "USER", "detail": "observado"}


def test_prepare_manage_reference_ids_stay_caller_provided(wired):
    diag = _seeded(wired)
    resp = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_evidence_link",
            payload={
                "evidence_id": EV1,
                "relation": "SUPPORTS",
                "target_id": "anything",
            },
        ),
    )
    assert resp.status_code == 200
    payload = _body(resp)["data"]["exact_change"]["payload"]
    assert payload["evidence_id"] == EV1  # existing reference preserved
    assert payload["link_id"]  # new link id server-generated


def test_prepare_manage_requires_authentication(wired):
    request = _request()
    request.state.user = None
    resp = routes.prepare_manage_diagnostic(
        request,
        str(uuid4()),
        routes.DiagnosticManagePrepareBody(
            action="add_finding", payload={"statement": "x"}
        ),
    )
    assert resp.status_code == 401


def test_prepare_manage_denies_service_principal(wired):
    resp = routes.prepare_manage_diagnostic(
        _request(_user(principal_type="service")),
        str(uuid4()),
        routes.DiagnosticManagePrepareBody(
            action="add_finding", payload={"statement": "x"}
        ),
    )
    assert resp.status_code == 403


def test_prepare_manage_all_13_actions_are_recognized(wired):
    diag = _seeded(wired)
    assert len(MANAGE_ACTIONS) == 13
    for action in sorted(MANAGE_ACTIONS):
        key = "conclusion_id" if action.endswith("conclusion") else "hypothesis_id"
        payload = {"statement": "s"} if action.startswith("add_") else {key: "x"}
        if action == "add_causal_link":
            payload = {"source_hypothesis_id": "h", "target_id": "t"}
        if action == "add_evidence_link":
            payload = {"evidence_id": EV1, "relation": "SUPPORTS"}
        resp = routes.prepare_manage_diagnostic(
            _request(),
            diag.diagnostic_id,
            routes.DiagnosticManagePrepareBody(action=action, payload=payload),
        )
        # 200 (proposal) — never 422 unsupported_action
        data = _body(resp)["data"] or {}
        assert data.get("error_code") != "unsupported_action", action
        assert resp.status_code == 200, action


# ---------------------------------------------------------------------------
# COMMIT
# ---------------------------------------------------------------------------


def _prepare_create(request, revision_id=REV_A, statement="raiz"):
    resp = routes.prepare_create_diagnostic(
        request,
        revision_id,
        routes.DiagnosticCreatePrepareBody(problem_statement=statement),
    )
    assert resp.status_code == 200
    return _body(resp)["data"]


def test_commit_requires_authentication(wired):
    request = _request()
    request.state.user = None
    resp = routes.commit_governed_proposal(
        request,
        routes.GovernedProposalCommitBody(
            proposal_handle="any", confirmation=True
        ),
    )
    assert resp.status_code == 401


def test_commit_denies_missing_access_permission(wired):
    resp = routes.commit_governed_proposal(
        _request(_user(permissions=[])),
        routes.GovernedProposalCommitBody(
            proposal_handle="any", confirmation=True
        ),
    )
    assert resp.status_code == 403


def test_commit_requires_confirmation_true(wired):
    proposal = _prepare_create(_request())
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=False,
        ),
    )
    assert resp.status_code == 422
    assert _body(resp)["data"]["error_code"] == "CONFIRMATION_REQUIRED"


def test_commit_actor_mismatch_is_denied(wired, notified):
    proposal = _prepare_create(_request())
    _prime_act_ctx()
    resp = routes.commit_governed_proposal(
        _request(_user(id=OTHER_USER_ID)),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert resp.status_code == 403
    assert _body(resp)["data"]["error_code"] == "proposal_actor_mismatch"
    assert notified == []


def test_commit_stale_proposal_is_409(wired, notified):
    proposal = _prepare_create(_request())
    _prime_act_ctx()
    # Current state drifted since PREPARE: a diagnostic now exists at the id.
    change = proposal["exact_change"]
    wired.seed(
        _diagnostic(
            diagnostic_id=change["diagnostic_id"],
            problem_statement=ProblemStatement("drifted"),
        )
    )
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert resp.status_code == 409
    assert _body(resp)["data"]["error_code"] == "proposal_stale"
    assert notified == []


def test_commit_service_principal_denied_at_fresh_authz(
    wired, rbac, notified
):
    proposal = _prepare_create(_request())
    # Same actor id but a service principal: actor binding passes, fresh
    # Core AuthZ denies the material write (principal_type != user).
    _prime_act_ctx(_user(principal_type="service"))
    resp = routes.commit_governed_proposal(
        _request(_user(principal_type="service")),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert resp.status_code == 403
    assert notified == []


def test_commit_core_unavailable_is_503(wired, rbac, notified):
    proposal = _prepare_create(_request())
    rbac.fail = True
    _prime_act_ctx()
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert resp.status_code == 503
    assert notified == []


def test_commit_valid_act_writes_and_verifies(wired, rbac, notified):
    proposal = _prepare_create(_request())
    _prime_act_ctx()
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert resp.status_code == 200
    data = _body(resp)["data"]
    assert data["postcondition"]["verified"] is True
    assert data["data"]["diagnostic"]["revision_id"] == REV_A
    # Canonical write path ran exactly once.
    assert wired.create.call_count == 1
    # Fresh Core /me ran at ACT (force_refresh=True).
    assert rbac.calls == [True]
    # Verified ACT → exactly one invalidation event.
    assert len(notified) == 1


def test_commit_manage_valid_act(wired, rbac, notified):
    diag = _seeded(wired)
    prep = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_finding", payload={"statement": "sintoma"}
        ),
    )
    handle = _body(prep)["data"]["proposal_handle"]
    _prime_act_ctx()
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=handle, confirmation=True
        ),
    )
    assert resp.status_code == 200
    assert wired.save.call_count == 1
    updated = wired.get(diag.diagnostic_id)
    assert len(updated.findings) == 1
    assert len(notified) == 1
    assert notified[0]["action"] == "update"


def test_commit_outcome_verification_failure_reports_no_success(
    wired, rbac, notified, monkeypatch
):
    proposal = _prepare_create(_request())
    _prime_act_ctx()
    monkeypatch.setattr(
        "tm_app.application.governed_writes.orchestrator._diag_verify",
        MagicMock(side_effect=RuntimeError("view diverged")),
    )
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert resp.status_code == 409
    assert _body(resp)["data"]["error_code"] == "outcome_verification_failed"
    assert notified == []


# ---------------------------------------------------------------------------
# REALTIME — emission contract + data minimization
# ---------------------------------------------------------------------------


def test_verified_act_emits_minimal_diagnostic_event(wired, rbac, notified):
    proposal = _prepare_create(_request(client_id="tab-42"))
    _prime_act_ctx()
    request = _request(client_id="tab-42")
    routes.commit_governed_proposal(
        request,
        routes.GovernedProposalCommitBody(
            proposal_handle=proposal["proposal_handle"],
            confirmation=True,
        ),
    )
    assert len(notified) == 1
    call = notified[0]
    assert call["entity_type"] == "diagnostic"
    assert call["entity_id"] == proposal["exact_change"]["diagnostic_id"]
    assert call["action"] == "create"
    assert call["actor_client_id"] == "tab-42"
    # Data minimization: authorized contract is exactly {"revision_id"} —
    # no content, no legacy revisao_id key over WS.
    assert call["payload"] == {"revision_id": REV_A}
    for forbidden in (
        "revisao_id",
        "problem_statement",
        "finding",
        "hypothesis",
        "conclusion",
        "evidence",
        "rationale",
        "provenance",
    ):
        assert forbidden not in call["payload"]


def test_diagnostic_section_key_and_revision_room():
    assert infer_section_key("diagnostic", "create") == "diagnostico"
    assert infer_section_key("diagnostic", "update") == "diagnostico"
    rooms = _related_rooms("diagnostic", "d1", {"revision_id": "r9"})
    assert "revisao:r9" in rooms
    assert "diagnostic:d1" in rooms


# ---------------------------------------------------------------------------
# CONCLUSION READ-BACK — projection/domain alignment regression
# (EXECUTION_DRIFT fix: project_conclusion reads domain ``root_cause``)
# ---------------------------------------------------------------------------


def _validated_current_hypothesis() -> Hypothesis:
    return Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
    )


def test_get_route_with_conclusion_without_root_cause(wired):
    conclusion = DiagnosticConclusion(
        conclusion_id=str(uuid4()), statement="c"
    )
    diag = _diagnostic(diagnostic_conclusions=[conclusion])
    wired.seed(diag)
    resp = routes.get_diagnostic(_request(), diag.diagnostic_id)
    assert resp.status_code == 200
    projected = _body(resp)["data"]["diagnostic"]["conclusions"][0]
    assert projected["conclusion_id"] == conclusion.conclusion_id
    assert projected["root_cause_hypothesis_id"] is None
    assert projected["epistemic_state"] == "INFERRED"


def test_get_route_with_conclusion_and_designated_root_cause(wired):
    h = _validated_current_hypothesis()
    conclusion = DiagnosticConclusion(
        conclusion_id=str(uuid4()),
        statement="c",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    diag = _diagnostic(hypotheses=[h], diagnostic_conclusions=[conclusion])
    wired.seed(diag)
    resp = routes.get_diagnostic(_request(), diag.diagnostic_id)
    assert resp.status_code == 200
    projected = _body(resp)["data"]["diagnostic"]["conclusions"][0]
    assert projected["root_cause_hypothesis_id"] == h.hypothesis_id
    assert projected["lifecycle"] == "VALIDATED"
    assert projected["epistemic_state"] == "INFERRED"


def test_get_route_with_validated_degraded_conclusion(wired):
    """VALIDATED + STALE_EVIDENCE rehydrates and projects verbatim."""
    h = Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
    )
    conclusion = DiagnosticConclusion(
        conclusion_id=str(uuid4()),
        statement="c",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    diag = _diagnostic(hypotheses=[h], diagnostic_conclusions=[conclusion])
    wired.seed(diag)
    resp = routes.get_diagnostic(_request(), diag.diagnostic_id)
    assert resp.status_code == 200
    projected = _body(resp)["data"]["diagnostic"]["conclusions"][0]
    assert projected["lifecycle"] == "VALIDATED"
    assert projected["effective_validation"] == "STALE_EVIDENCE"
    assert projected["root_cause_hypothesis_id"] == h.hypothesis_id


def test_list_route_counts_conclusions(wired):
    h = _validated_current_hypothesis()
    conclusion = DiagnosticConclusion(
        conclusion_id=str(uuid4()),
        statement="c",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    diag = _diagnostic(
        hypotheses=[h],
        diagnostic_conclusions=[
            conclusion,
            DiagnosticConclusion(
                conclusion_id=str(uuid4()), statement="c2"
            ),
        ],
    )
    wired.seed(diag)
    resp = routes.list_diagnostics(_request(), REV_A)
    assert resp.status_code == 200
    item = _body(resp)["data"]["items"][0]
    assert item["conclusions_count"] == 2
    assert item["has_validated_conclusion"] is True
    assert item["revalidation_attention_required"] is False
    assert "conclusions" not in item


def test_add_conclusion_commit_then_get(wired, rbac, notified):
    diag = _seeded(wired)
    prep = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="add_conclusion",
            payload={
                "statement": "conclusão governada",
                "rationale": "porque",
            },
        ),
    )
    assert prep.status_code == 200
    handle = _body(prep)["data"]["proposal_handle"]
    _prime_act_ctx()
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=handle, confirmation=True
        ),
    )
    assert resp.status_code == 200
    assert _body(resp)["data"]["postcondition"]["verified"] is True
    # Authoritative read-back through the canonical GET — no 500.
    back = routes.get_diagnostic(_request(), diag.diagnostic_id)
    assert back.status_code == 200
    conclusions = _body(back)["data"]["diagnostic"]["conclusions"]
    assert len(conclusions) == 1
    assert conclusions[0]["statement"] == "conclusão governada"
    assert conclusions[0]["root_cause_hypothesis_id"] is None
    assert conclusions[0]["lifecycle"] == "DRAFT"


def test_validate_conclusion_commit_then_get(wired, rbac, notified):
    h = _validated_current_hypothesis()
    conclusion = DiagnosticConclusion(
        conclusion_id=str(uuid4()),
        statement="c",
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    diag = _diagnostic(hypotheses=[h], diagnostic_conclusions=[conclusion])
    wired.seed(diag)
    prep = routes.prepare_manage_diagnostic(
        _request(),
        diag.diagnostic_id,
        routes.DiagnosticManagePrepareBody(
            action="validate_conclusion",
            payload={"conclusion_id": conclusion.conclusion_id},
        ),
    )
    assert prep.status_code == 200
    handle = _body(prep)["data"]["proposal_handle"]
    _prime_act_ctx()
    resp = routes.commit_governed_proposal(
        _request(),
        routes.GovernedProposalCommitBody(
            proposal_handle=handle, confirmation=True
        ),
    )
    assert resp.status_code == 200
    assert _body(resp)["data"]["postcondition"]["verified"] is True
    back = routes.get_diagnostic(_request(), diag.diagnostic_id)
    assert back.status_code == 200
    projected = _body(back)["data"]["diagnostic"]["conclusions"][0]
    assert projected["lifecycle"] == "VALIDATED"
    assert projected["epistemic_state"] == "INFERRED"
    assert projected["effective_validation"] == "CURRENT"
    assert projected["root_cause_hypothesis_id"] == h.hypothesis_id
