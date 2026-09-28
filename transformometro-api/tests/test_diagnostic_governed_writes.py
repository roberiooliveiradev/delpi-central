"""Diagnostic V1 — governed PREPARE/ACT integration tests.

Exercises the canonical ``GovernedWriteOrchestrator`` with the real
``FreshAuthorizationAdapter`` (Core lookup monkeypatched) so every ACT
goes through the same fresh, fail-closed authorization path as runtime.
"""

from __future__ import annotations

import time
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

from tm_app.application.governed_writes.errors import (
    BUSINESS_RULE,
    CONFLICT,
    FORBIDDEN,
    NOT_FOUND,
    OUTCOME_VERIFICATION_FAILED,
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_EXPIRED,
    PROPOSAL_MISMATCH,
    PROPOSAL_NOT_FOUND,
    PROPOSAL_REQUIRED,
    PROPOSAL_STALE,
    VALIDATION,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (
    GovernedWriteOrchestrator,
)
from tm_app.application.governed_writes.diagnostic_capabilities import (
    MANAGE_ACTIONS,
    DiagnosticWriteStack,
    parse_manage_payload,
)
from tm_app.application.governed_writes.proposal_store import (
    get_proposal_store,
    reset_proposal_store_for_tests,
)
from tm_app.application.ports.evidence_reader_port import EvidenceRef
from tm_app.application.ports.revision_reader_port import RevisionContext
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
    MANAGE_PERMISSION,
)
from tm_app.application.use_cases.diagnostic_write import DiagnosticWriteUseCase
from tm_app.domain.diagnostic.diagnostic import (
    ClaimLifecycle,
    Diagnostic,
    EffectiveValidation,
    EpistemicState,
    Finding,
    Hypothesis,
    ProblemStatement,
)
from tm_app.infrastructure.security.diagnostic_authorization import (
    FreshAuthorizationAdapter,
)

REV_A = str(uuid4())
EV1 = str(uuid4())
USER_ID = "u-actor-1"


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
    """Monkeypatched ``load_user_rbac`` — emulates fresh Core answers."""

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
        name="Actor",
        is_superadmin=False,
        permissions=[ACCESS_PERMISSION],
        principal_type="user",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _request(user=None) -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "https",
        "path": "/governed",
        "raw_path": b"/governed",
        "query_string": b"",
        "headers": [],
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


def _orch(repo=None) -> tuple[GovernedWriteOrchestrator, FakeDiagnosticRepo]:
    repo = repo or FakeDiagnosticRepo()
    return GovernedWriteOrchestrator(diagnostic_stack=_stack(repo)), repo


def _diagnostic(**kwargs) -> Diagnostic:
    kwargs.setdefault("problem_statement", ProblemStatement("problema"))
    return Diagnostic(diagnostic_id=str(uuid4()), revision_id=REV_A, **kwargs)


def _prime_act_ctx(user=None):
    """Contextvars the FreshAuthorizationAdapter resolves at ACT."""
    set_current_user(user or _user())
    set_request_authorization("Bearer tok")


def _code(excinfo) -> str:
    return excinfo.value.code


# ---------------------------------------------------------------------------
# ACTION INVENTORY + STRICT ENVELOPE
# ---------------------------------------------------------------------------


EXPECTED_MANAGE_ACTIONS = {
    "add_finding",
    "add_hypothesis",
    "add_causal_link",
    "add_evidence_link",
    "add_conclusion",
    "validate_hypothesis",
    "reject_hypothesis",
    "supersede_hypothesis",
    "mark_hypothesis_stale_evidence",
    "mark_hypothesis_revalidation_required",
    "validate_conclusion",
    "reject_conclusion",
    "supersede_conclusion",
}


def test_manage_action_inventory_is_exactly_13():
    assert len(MANAGE_ACTIONS) == 13
    assert MANAGE_ACTIONS == EXPECTED_MANAGE_ACTIONS


@pytest.mark.parametrize("action", sorted(EXPECTED_MANAGE_ACTIONS))
def test_every_manage_action_parses_explicitly(action):
    # Each allowlisted action must reach its own explicit parser — never a
    # generic passthrough.
    payload = {
        "add_finding": {"finding_id": "f", "statement": "s"},
        "add_hypothesis": {"hypothesis_id": "h", "statement": "s"},
        "add_causal_link": {
            "link_id": "l", "source_hypothesis_id": "h", "target_id": "f",
        },
        "add_evidence_link": {
            "link_id": "l", "evidence_id": "e", "relation": "SUPPORTS",
        },
        "add_conclusion": {"conclusion_id": "c", "statement": "s"},
    }.get(action) or {"hypothesis_id": "h"}
    if action in {"validate_conclusion", "reject_conclusion",
                  "supersede_conclusion"}:
        payload = {"conclusion_id": "c"}
    normalized = parse_manage_payload(action, payload)
    assert normalized
    assert "lifecycle" not in normalized
    assert "effective_validation" not in normalized


def test_prepare_create_rejects_extra_top_level_fields(rbac):
    orch, repo = _orch()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(),
            capability="create_diagnostic",
            args={
                "diagnostic_id": "d-1",
                "revision_id": REV_A,
                "problem_statement": "p",
                "silently_ignored_field": True,
            },
        )
    assert _code(excinfo) == VALIDATION
    assert len(get_proposal_store()._items) == 0
    repo.create.assert_not_called()


def test_prepare_manage_rejects_extra_top_level_fields(rbac):
    orch, repo = _orch()
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(),
            capability="manage_diagnostic",
            args={
                "diagnostic_id": diag.diagnostic_id,
                "action": "add_finding",
                "payload": {"finding_id": "f", "statement": "s"},
                "extra_envelope_field": "x",
            },
        )
    assert _code(excinfo) == VALIDATION
    assert len(get_proposal_store()._items) == 0
    repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# PREPARE
# ---------------------------------------------------------------------------


def test_prepare_create_success(rbac):
    orch, repo = _orch()
    result = orch.prepare(
        _request(),
        capability="create_diagnostic",
        args={
            "diagnostic_id": "d-1",
            "revision_id": REV_A,
            "problem_statement": "  problema X ",
        },
    )
    assert result["proposal_handle"]
    assert result["act_allowed"] is True
    change = result["exact_change"]
    assert change == {
        "action": "create",
        "diagnostic_id": "d-1",
        "revision_id": REV_A,
        "problem_statement": "problema X",
        "provenance": None,
    }
    assert result["confirmation_requirement"]["explicit_user_confirmation"]
    repo.create.assert_not_called()  # PREPARE never persists


def test_prepare_manage_success_seals_normalized_payload(rbac):
    orch, repo = _orch()
    diag = _diagnostic()
    repo.seed(diag)
    result = orch.prepare(
        _request(),
        capability="manage_diagnostic",
        args={
            "diagnostic_id": diag.diagnostic_id,
            "action": "add_finding",
            "payload": {"finding_id": "f-1", "statement": "sintoma"},
        },
    )
    change = result["exact_change"]
    assert change["action"] == "add_finding"
    assert change["payload"]["finding_id"] == "f-1"
    assert change["expected_version"] == diag.version
    assert result["current_state_fingerprint"]
    repo.save.assert_not_called()


@pytest.mark.parametrize(
    "action,payload",
    [
        ("validate_hypothesis", {"hypothesis_id": "h-1"}),
        ("mark_hypothesis_stale_evidence", {"hypothesis_id": "h-1"}),
        ("validate_conclusion", {"conclusion_id": "c-1", "note": "ok"}),
    ],
)
def test_prepare_manage_families(rbac, action, payload):
    orch, repo = _orch()
    diag = _diagnostic()
    repo.seed(diag)
    result = orch.prepare(
        _request(),
        capability="manage_diagnostic",
        args={
            "diagnostic_id": diag.diagnostic_id,
            "action": action,
            "payload": payload,
        },
    )
    assert result["act_allowed"] is True
    assert result["exact_change"]["action"] == action


def test_prepare_unknown_action_rejected(rbac):
    orch, repo = _orch()
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(),
            capability="manage_diagnostic",
            args={
                "diagnostic_id": diag.diagnostic_id,
                "action": "execute_anything",
                "payload": {},
            },
        )
    assert _code(excinfo) == VALIDATION


def test_prepare_rejects_kernel_owned_fields(rbac):
    orch, repo = _orch()
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(),
            capability="manage_diagnostic",
            args={
                "diagnostic_id": diag.diagnostic_id,
                "action": "add_hypothesis",
                "payload": {
                    "hypothesis_id": "h-1",
                    "statement": "causa",
                    "lifecycle": "VALIDATED",
                },
            },
        )
    assert _code(excinfo) == VALIDATION


def test_prepare_manage_missing_diagnostic(rbac):
    orch, _ = _orch()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(),
            capability="manage_diagnostic",
            args={
                "diagnostic_id": str(uuid4()),
                "action": "add_finding",
                "payload": {"finding_id": "f", "statement": "s"},
            },
        )
    assert _code(excinfo) == NOT_FOUND


def test_prepare_create_missing_revision(rbac):
    orch, repo = _orch()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(),
            capability="create_diagnostic",
            args={
                "diagnostic_id": "d-1",
                "revision_id": str(uuid4()),
                "problem_statement": "p",
            },
        )
    assert _code(excinfo) == NOT_FOUND
    repo.create.assert_not_called()


def test_prepare_service_principal_denied(rbac):
    orch, repo = _orch()
    svc = _user(principal_type="service", is_superadmin=True)
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(svc),
            capability="create_diagnostic",
            args={
                "diagnostic_id": "d-1",
                "revision_id": REV_A,
                "problem_statement": "p",
            },
        )
    assert _code(excinfo) == FORBIDDEN
    repo.create.assert_not_called()


def test_prepare_missing_access_denied(rbac):
    orch, repo = _orch()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(_user(permissions=[])),
            capability="create_diagnostic",
            args={
                "diagnostic_id": "d-1",
                "revision_id": REV_A,
                "problem_statement": "p",
            },
        )
    assert _code(excinfo) == FORBIDDEN
    repo.create.assert_not_called()


def test_prepare_manage_only_permission_denied(rbac):
    orch, repo = _orch()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.prepare(
            _request(_user(permissions=[MANAGE_PERMISSION])),
            capability="create_diagnostic",
            args={
                "diagnostic_id": "d-1",
                "revision_id": REV_A,
                "problem_statement": "p",
            },
        )
    assert _code(excinfo) == FORBIDDEN
    repo.create.assert_not_called()


def test_prepare_evidence_out_of_revision_marks_not_ready(rbac):
    orch, repo = _orch()
    diag = _diagnostic()
    repo.seed(diag)
    result = orch.prepare(
        _request(),
        capability="manage_diagnostic",
        args={
            "diagnostic_id": diag.diagnostic_id,
            "action": "add_evidence_link",
            "payload": {
                "link_id": "el-1",
                "evidence_id": str(uuid4()),
                "relation": "SUPPORTS",
            },
        },
    )
    assert result["act_allowed"] is False
    assert "evidence_out_of_revision" in (
        result["validation_result"].get("missing") or []
    )


# ---------------------------------------------------------------------------
# ACT
# ---------------------------------------------------------------------------


def _prepare(rbac, repo=None, diag=None, action="add_finding", payload=None):
    orch, repo = _orch(repo)
    if diag is not None:
        repo.seed(diag)
    request = _request()
    if action == "create":
        return orch, repo, orch.prepare(
            request,
            capability="create_diagnostic",
            args={
                "diagnostic_id": diag.diagnostic_id if diag else "d-1",
                "revision_id": REV_A,
                "problem_statement": "problema",
            },
        )
    return orch, repo, orch.prepare(
        request,
        capability="manage_diagnostic",
        args={
            "diagnostic_id": diag.diagnostic_id,
            "action": action,
            "payload": payload or {"finding_id": "f-1", "statement": "s"},
        },
    )


def test_act_create_executes_and_verifies(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    _prime_act_ctx()
    result = orch.act(
        _request(),
        capability="create_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    assert result["verified"] is True
    repo.create.assert_called_once()
    assert result["data"]["diagnostic"]["diagnostic_id"] == "d-1"
    assert rbac.calls == [True]  # fresh lookup, not cached


def test_act_add_finding_end_to_end(rbac):
    diag = _diagnostic()
    orch, repo, prepared = _prepare(rbac, diag=diag)
    _prime_act_ctx()
    result = orch.act(
        _request(),
        capability="manage_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    assert result["verified"] is True
    view = result["data"]["diagnostic"]
    assert view["findings"][0]["finding_id"] == "f-1"
    repo.save.assert_called_once()


def test_act_validate_hypothesis_lifecycle(rbac):
    hyp = Hypothesis("h-1", "causa")
    diag = _diagnostic(hypotheses=[hyp])
    orch, repo, prepared = _prepare(
        rbac, diag=diag, action="validate_hypothesis",
        payload={"hypothesis_id": "h-1"},
    )
    _prime_act_ctx()
    result = orch.act(
        _request(),
        capability="manage_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    assert result["verified"] is True
    hyp_view = result["data"]["diagnostic"]["hypotheses"][0]
    assert hyp_view["lifecycle"] == "VALIDATED"
    assert hyp_view["epistemic_state"] == "INFERRED"


def test_act_wrong_actor_denied(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    _prime_act_ctx(_user(id="other-actor"))
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(_user(id="other-actor")),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_ACTOR_MISMATCH
    repo.create.assert_not_called()


def test_act_wrong_capability_denied(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="manage_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_MISMATCH


def test_act_invalid_handle_denied(rbac):
    orch, _ = _orch()
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="create_diagnostic",
            proposal_handle="bogus",
        )
    assert _code(excinfo) in (PROPOSAL_NOT_FOUND, PROPOSAL_REQUIRED, VALIDATION)


def test_act_single_use(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    _prime_act_ctx()
    orch.act(
        _request(),
        capability="create_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_NOT_FOUND
    repo.create.assert_called_once()


def test_act_expired_proposal(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    store = get_proposal_store()
    proposal = next(iter(store._items.values()))
    proposal.expires_at = time.time() - 1
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_EXPIRED
    repo.create.assert_not_called()


def test_act_stale_state_rejected(rbac):
    diag = _diagnostic()
    orch, repo, prepared = _prepare(rbac, diag=diag)
    # Material change between PREPARE and ACT — fingerprint must break.
    diag.add_finding(Finding("f-x", "concorrente"))
    object.__setattr__(diag, "_version", diag.version + 1)
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="manage_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_STALE
    assert excinfo.value.status_code == 409
    repo.save.assert_not_called()


def test_act_permission_revoked_after_prepare_denied(rbac):
    """CRITICAL: PREPARE ok → permission removed → ACT fresh lookup denies."""
    orch, repo, prepared = _prepare(rbac, action="create")
    rbac.permissions = []  # T1: revoked in Core
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == FORBIDDEN
    assert excinfo.value.status_code == 403
    assert rbac.calls == [True]  # fresh Core lookup happened at ACT
    repo.create.assert_not_called()


def test_act_core_unavailable_fails_closed(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    rbac.fail = True
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == "authorization_unavailable"
    assert excinfo.value.status_code == 503
    repo.create.assert_not_called()


def test_act_service_principal_denied(rbac):
    orch, repo, prepared = _prepare(rbac, action="create")
    _prime_act_ctx(_user(principal_type="service", is_superadmin=True))
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(_user(principal_type="service", is_superadmin=True)),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == FORBIDDEN
    assert rbac.calls == []  # denied before reaching the authority
    repo.create.assert_not_called()


def test_act_domain_violation_no_success(rbac):
    diag = _diagnostic()  # no hypotheses
    orch, repo, prepared = _prepare(
        rbac, diag=diag, action="validate_hypothesis",
        payload={"hypothesis_id": "missing"},
    )
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="manage_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == VALIDATION
    repo.save.assert_not_called()


def test_act_concurrency_conflict(rbac):
    diag = _diagnostic()
    orch, repo, prepared = _prepare(rbac, diag=diag)

    def raced_save(d, *, expected_version):
        err = RuntimeError("lost update")
        err.code = "diagnostic.concurrent_modification"
        raise err

    repo.save = MagicMock(side_effect=raced_save)
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="manage_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == CONFLICT
    assert excinfo.value.status_code == 409


def test_act_divergent_readback_no_verified_success(rbac):
    diag = _diagnostic()
    orch, repo, prepared = _prepare(rbac, diag=diag)

    original_get = repo.get

    def divergent_get(diagnostic_id):
        # Returns a *fresh, unmutated* aggregate identical to the PREPARE
        # state: fingerprint recompute matches, the save "succeeds", but the
        # authoritative read-back never observes the mutation → must be
        # OUTCOME_VERIFICATION_FAILED, never a verified success.
        d = original_get(diagnostic_id)
        return Diagnostic(
            diagnostic_id=d.diagnostic_id,
            revision_id=d.revision_id,
            problem_statement=d.problem_statement,
            version=d.version,
            findings=tuple(d.findings),
            hypotheses=tuple(d.hypotheses),
            causal_links=tuple(d.causal_links),
            evidence_links=tuple(d.evidence_links),
            diagnostic_conclusions=tuple(d.diagnostic_conclusions),
        )

    repo.get = divergent_get  # type: ignore[assignment]
    _prime_act_ctx()
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request(),
            capability="manage_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == OUTCOME_VERIFICATION_FAILED
    assert excinfo.value.status_code == 409


@pytest.mark.parametrize(
    "action,target_key,target_field,target_value",
    [
        ("reject_hypothesis", "hypotheses", "lifecycle", "REJECTED"),
        ("supersede_hypothesis", "hypotheses", "lifecycle", "SUPERSEDED"),
        (
            "mark_hypothesis_revalidation_required",
            "hypotheses",
            "effective_validation",
            "REVALIDATION_REQUIRED",
        ),
        ("reject_conclusion", "diagnostic_conclusions", "lifecycle", "REJECTED"),
        (
            "supersede_conclusion",
            "diagnostic_conclusions",
            "lifecycle",
            "SUPERSEDED",
        ),
    ],
)
def test_act_remaining_actions_explicit_dispatch(
    rbac, action, target_key, target_field, target_value
):
    # Every allowlisted action must reach its explicit use-case branch and
    # produce its declared postcondition — never a generic branch.
    if "hypothesis" in action:
        lifecycle = (
            ClaimLifecycle.VALIDATED if action == "supersede_hypothesis"
            else ClaimLifecycle.DRAFT
        )
        diag = _diagnostic(
            hypotheses=[Hypothesis("h-1", "causa", lifecycle=lifecycle)]
        )
        payload = {"hypothesis_id": "h-1"}
    else:
        lifecycle = (
            ClaimLifecycle.VALIDATED
            if action == "supersede_conclusion"
            else ClaimLifecycle.DRAFT
        )
        from tm_app.domain.diagnostic.diagnostic import DiagnosticConclusion

        diag = _diagnostic(
            diagnostic_conclusions=[
                DiagnosticConclusion("c-1", "concl", lifecycle=lifecycle)
            ]
        )
        payload = {"conclusion_id": "c-1"}

    orch, repo, prepared = _prepare(rbac, diag=diag, action=action,
                                    payload=payload)
    _prime_act_ctx()
    result = orch.act(
        _request(),
        capability="manage_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    assert result["verified"] is True
    items = result["data"]["diagnostic"][target_key]
    assert items[0][target_field] == target_value
    repo.save.assert_called_once()


def test_act_mark_stale_effective_validation(rbac):
    hyp = Hypothesis("h-1", "causa")
    diag = _diagnostic(hypotheses=[hyp])
    orch, repo, prepared = _prepare(
        rbac, diag=diag, action="mark_hypothesis_stale_evidence",
        payload={"hypothesis_id": "h-1"},
    )
    _prime_act_ctx()
    result = orch.act(
        _request(),
        capability="manage_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    hyp_view = result["data"]["diagnostic"]["hypotheses"][0]
    assert hyp_view["effective_validation"] == "STALE_EVIDENCE"
    assert hyp_view["lifecycle"] == "DRAFT"
