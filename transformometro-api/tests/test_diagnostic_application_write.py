"""Diagnostic V1 — Application governed-write tests.

Unit layer proves the orchestration contract: fresh fail-closed AuthZ,
end-user principal requirement, revision-scoped evidence check,
optimistic concurrency, authoritative read-back and per-intent
postconditions — with in-memory fakes of the ports only.
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tm_app.application.ports.authorization_port import (
    AuthorizationPrincipal,
    DiagnosticAuthorizationError,
)
from tm_app.application.ports.evidence_reader_port import EvidenceRef
from tm_app.application.ports.revision_reader_port import RevisionContext
from tm_app.application.security.transformometro_permissions import (
    ACCESS_PERMISSION,
)
from tm_app.application.use_cases.diagnostic_write import (
    DiagnosticWriteError,
    DiagnosticWriteUseCase,
)
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
from delpi_auth.request_context import (
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)
from tm_app.infrastructure.security.diagnostic_authorization import (
    FreshAuthorizationAdapter,
)

REV_A = str(uuid4())
EV1 = str(uuid4())
EV_FOREIGN = str(uuid4())


def run(coro):
    return asyncio.run(coro)


# ---------------------------------------------------------------------------
# Fakes (ports only)
# ---------------------------------------------------------------------------


class FakeAuthorization:
    def __init__(self, exc: Exception | None = None) -> None:
        self.exc = exc
        self.calls = 0

    async def authorize_fresh(self) -> AuthorizationPrincipal:
        self.calls += 1
        if self.exc is not None:
            raise self.exc
        return AuthorizationPrincipal(
            user_id=str(uuid4()),
            email="user@delpi",
            is_superadmin=False,
            permissions=(ACCESS_PERMISSION,),
            principal_type="user",
            rbac_fresh=True,
        )


class FakeRevisionReader:
    def __init__(self) -> None:
        self._store = {
            REV_A: RevisionContext(
                revision_id=REV_A,
                processo_id=str(uuid4()),
                instancia_id=str(uuid4()),
                versao_revisao="v1",
                cenario_tipo="as_is",
                revisao_referencia_id=None,
            )
        }

    def get(self, revision_id):
        return self._store.get(revision_id)


class FakeEvidenceReader:
    def list_by_revision(self, revision_id):
        if revision_id == REV_A:
            return [EvidenceRef(EV1, REV_A, "anexo", "e.pdf", None)]
        return []


class FakeDiagnosticRepo:
    """Emulates the persistence contract: version-guarded save, read-back."""

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


def _use_case(repo=None, authz=None) -> tuple[DiagnosticWriteUseCase, object]:
    repo = repo or FakeDiagnosticRepo()
    use_case = DiagnosticWriteUseCase(
        diagnostics=repo,
        revisions=FakeRevisionReader(),
        evidence=FakeEvidenceReader(),
        authorization=authz or FakeAuthorization(),
    )
    return use_case, repo


def _diagnostic(**kwargs) -> Diagnostic:
    kwargs.setdefault("problem_statement", ProblemStatement("problema base"))
    return Diagnostic(
        diagnostic_id=str(uuid4()), revision_id=REV_A, **kwargs
    )


def _hypothesis(**kwargs) -> Hypothesis:
    return Hypothesis(hypothesis_id=str(uuid4()), statement="causa", **kwargs)


def _code(excinfo) -> str:
    return excinfo.value.code


# ---------------------------------------------------------------------------
# AuthN / AuthZ gates
# ---------------------------------------------------------------------------


def test_missing_authn_denies_and_does_not_persist():
    authz = FakeAuthorization(
        DiagnosticAuthorizationError(
            "diagnostic.authentication_required", "não autenticado"
        )
    )
    use_case, repo = _use_case(authz=authz)
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(use_case.add_finding(
            diagnostic_id=diag.diagnostic_id,
            finding=Finding("f1", "achado"),
        ))
    assert _code(excinfo) == "diagnostic.authentication_required"
    repo.save.assert_not_called()


def test_missing_access_denies_and_does_not_persist():
    authz = FakeAuthorization(
        DiagnosticAuthorizationError(
            "diagnostic.authorization_denied", "sem access"
        )
    )
    use_case, repo = _use_case(authz=authz)
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(use_case.validate_hypothesis(
            diagnostic_id=diag.diagnostic_id, hypothesis_id="h1"
        ))
    assert _code(excinfo) == "diagnostic.authorization_denied"
    repo.save.assert_not_called()


def test_manage_without_access_is_denied():
    # AuthorizationPort is the only gate — a principal holding
    # transformometro.manage but not .access arrives denied from the
    # adapter; the use case must not bypass it.
    authz = FakeAuthorization(
        DiagnosticAuthorizationError(
            "diagnostic.authorization_denied",
            "Sem permissão transformometro.access.",
        )
    )
    use_case, repo = _use_case(authz=authz)
    with pytest.raises(DiagnosticAuthorizationError):
        run(use_case.create_diagnostic(
            diagnostic_id="d1", revision_id=REV_A,
            problem_statement="p",
        ))
    repo.create.assert_not_called()


def test_fresh_authority_unavailable_fails_closed():
    authz = FakeAuthorization(
        DiagnosticAuthorizationError(
            "diagnostic.authorization_unavailable", "Core indisponível"
        )
    )
    use_case, repo = _use_case(authz=authz)
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(use_case.mark_hypothesis_stale_evidence(
            diagnostic_id=diag.diagnostic_id, hypothesis_id="h1"
        ))
    assert _code(excinfo) == "diagnostic.authorization_unavailable"
    repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# FreshAuthorizationAdapter — canonical principal + freshness
# ---------------------------------------------------------------------------


def _ctx_user(**kwargs):
    defaults = dict(
        id="u1", email="u@delpi", is_superadmin=False,
        permissions=(ACCESS_PERMISSION,), principal_type="user",
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _reset_ctx():
    clear_current_user()
    clear_request_authorization()


def test_adapter_denies_without_authenticated_principal():
    _reset_ctx()
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(FreshAuthorizationAdapter().authorize_fresh())
    assert _code(excinfo) == "diagnostic.authentication_required"


def test_adapter_denies_service_principal(monkeypatch):
    _reset_ctx()
    called = []

    async def fake_rbac(token, *, force_refresh=False):
        called.append(force_refresh)
        return {"permissions": [ACCESS_PERMISSION]}

    monkeypatch.setattr(
        "tm_app.infrastructure.security.diagnostic_authorization.load_user_rbac",
        fake_rbac,
    )
    set_current_user(_ctx_user(principal_type="service"))
    set_request_authorization("Bearer tok")
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(FreshAuthorizationAdapter().authorize_fresh())
    assert _code(excinfo) == "diagnostic.authorization_denied"
    assert called == []  # service principal never reaches the authority
    _reset_ctx()


def test_adapter_fails_closed_when_authority_unavailable(monkeypatch):
    _reset_ctx()

    async def failing_rbac(token, *, force_refresh=False):
        assert force_refresh is True
        raise RuntimeError("Core down")

    monkeypatch.setattr(
        "tm_app.infrastructure.security.diagnostic_authorization.load_user_rbac",
        failing_rbac,
    )
    set_current_user(_ctx_user())
    set_request_authorization("Bearer tok")
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(FreshAuthorizationAdapter().authorize_fresh())
    assert _code(excinfo) == "diagnostic.authorization_unavailable"
    _reset_ctx()


def test_adapter_denies_user_without_access(monkeypatch):
    _reset_ctx()

    async def fake_rbac(token, *, force_refresh=False):
        return {"id": "u1", "permissions": [], "is_superadmin": False}

    monkeypatch.setattr(
        "tm_app.infrastructure.security.diagnostic_authorization.load_user_rbac",
        fake_rbac,
    )
    set_current_user(_ctx_user())
    set_request_authorization("Bearer tok")
    with pytest.raises(DiagnosticAuthorizationError) as excinfo:
        run(FreshAuthorizationAdapter().authorize_fresh())
    assert _code(excinfo) == "diagnostic.authorization_denied"
    _reset_ctx()


def test_adapter_returns_fresh_principal(monkeypatch):
    _reset_ctx()

    async def fake_rbac(token, *, force_refresh=False):
        assert force_refresh is True
        return {
            "id": "u1", "email": "u@delpi",
            "permissions": [ACCESS_PERMISSION], "is_superadmin": False,
        }

    monkeypatch.setattr(
        "tm_app.infrastructure.security.diagnostic_authorization.load_user_rbac",
        fake_rbac,
    )
    set_current_user(_ctx_user())
    set_request_authorization("Bearer tok")
    principal = run(FreshAuthorizationAdapter().authorize_fresh())
    assert principal.user_id == "u1"
    assert principal.rbac_fresh is True
    assert principal.principal_type == "user"
    _reset_ctx()


# ---------------------------------------------------------------------------
# create_diagnostic
# ---------------------------------------------------------------------------


def test_create_diagnostic_success_readback():
    use_case, repo = _use_case()
    view = run(use_case.create_diagnostic(
        diagnostic_id="d-1", revision_id=REV_A,
        problem_statement="  problema X  ",
    ))
    repo.create.assert_called_once()
    assert view.diagnostic_id == "d-1"
    assert view.revision_id == REV_A
    assert view.problem_statement.text == "problema X"
    assert view.version >= 1
    # detached read surface — no mutation methods
    assert not hasattr(view, "add_finding")


def test_create_diagnostic_missing_revision_denied():
    use_case, repo = _use_case()
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.create_diagnostic(
            diagnostic_id="d-1", revision_id=str(uuid4()),
            problem_statement="p",
        ))
    assert _code(excinfo) == "diagnostic.revision_not_found"
    repo.create.assert_not_called()


def test_create_diagnostic_empty_statement_domain_error():
    use_case, repo = _use_case()
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.create_diagnostic(
            diagnostic_id="d-1", revision_id=REV_A,
            problem_statement="   ",
        ))
    assert _code(excinfo) == "invalid_problem_statement"
    repo.create.assert_not_called()


# ---------------------------------------------------------------------------
# entity additions
# ---------------------------------------------------------------------------


def test_add_finding_persists_and_readback_verified():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    view = run(use_case.add_finding(
        diagnostic_id=diag.diagnostic_id,
        finding=Finding("f-1", "sintoma observado"),
    ))
    repo.save.assert_called_once()
    assert any(f.finding_id == "f-1" for f in view.findings)
    assert view.version > 1


def test_add_hypothesis_keeps_draft_and_inferred():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    view = run(use_case.add_hypothesis(
        diagnostic_id=diag.diagnostic_id, hypothesis=_hypothesis(),
    ))
    hyp = view.hypotheses[0]
    assert hyp.lifecycle is ClaimLifecycle.DRAFT
    assert hyp.epistemic_state is EpistemicState.INFERRED


def test_add_causal_link_persists():
    use_case, repo = _use_case()
    hyp = _hypothesis()
    finding = Finding("f-1", "sintoma")
    diag = _diagnostic(hypotheses=[hyp], findings=[finding])
    repo.seed(diag)
    view = run(use_case.add_causal_link(
        diagnostic_id=diag.diagnostic_id,
        link=CausalLink("cl-1", hyp.hypothesis_id, "f-1"),
    ))
    assert view.causal_links[0].link_id == "cl-1"


def test_add_conclusion_persists_draft():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    view = run(use_case.add_conclusion(
        diagnostic_id=diag.diagnostic_id,
        conclusion=DiagnosticConclusion("c-1", "conclusão"),
    ))
    assert view.diagnostic_conclusions[0].lifecycle is ClaimLifecycle.DRAFT


def test_mutation_on_missing_diagnostic():
    use_case, repo = _use_case()
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.add_finding(
            diagnostic_id=str(uuid4()), finding=Finding("f", "s"),
        ))
    assert _code(excinfo) == "diagnostic.not_found"
    repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# evidence revision check
# ---------------------------------------------------------------------------


def test_add_evidence_link_same_revision_allowed():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    view = run(use_case.add_evidence_link(
        diagnostic_id=diag.diagnostic_id,
        link=EvidenceLink("el-1", EV1, EvidenceRelation.SUPPORTS),
    ))
    assert view.evidence_links[0].evidence_id == EV1


def test_add_evidence_link_foreign_revision_denied_before_save():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.add_evidence_link(
            diagnostic_id=diag.diagnostic_id,
            link=EvidenceLink("el-1", EV_FOREIGN, EvidenceRelation.SUPPORTS),
        ))
    assert _code(excinfo) == "diagnostic.evidence_out_of_revision"
    repo.save.assert_not_called()


def test_add_evidence_link_contradicts_allowed():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    view = run(use_case.add_evidence_link(
        diagnostic_id=diag.diagnostic_id,
        link=EvidenceLink("el-1", EV1, EvidenceRelation.CONTRADICTS),
    ))
    assert view.evidence_links[0].relation is EvidenceRelation.CONTRADICTS


# ---------------------------------------------------------------------------
# lifecycle + effective validation mutations
# ---------------------------------------------------------------------------


def test_validate_hypothesis_postcondition():
    use_case, repo = _use_case()
    hyp = _hypothesis()
    diag = _diagnostic(hypotheses=[hyp])
    repo.seed(diag)
    view = run(use_case.validate_hypothesis(
        diagnostic_id=diag.diagnostic_id, hypothesis_id=hyp.hypothesis_id,
    ))
    persisted = view.hypotheses[0]
    assert persisted.lifecycle is ClaimLifecycle.VALIDATED
    assert persisted.epistemic_state is EpistemicState.INFERRED


def test_reject_and_supersede_hypothesis():
    use_case, repo = _use_case()
    h1 = _hypothesis()
    # SUPERSEDED exige origem VALIDATED — rehydrate a materialized state.
    h2 = Hypothesis(str(uuid4()), "causa", lifecycle=ClaimLifecycle.VALIDATED)
    diag = _diagnostic(hypotheses=[h1, h2])
    repo.seed(diag)
    v1 = run(use_case.reject_hypothesis(
        diagnostic_id=diag.diagnostic_id, hypothesis_id=h1.hypothesis_id,
    ))
    assert {h.hypothesis_id: h.lifecycle for h in v1.hypotheses}[
        h1.hypothesis_id] is ClaimLifecycle.REJECTED
    v2 = run(use_case.supersede_hypothesis(
        diagnostic_id=diag.diagnostic_id, hypothesis_id=h2.hypothesis_id,
    ))
    assert {h.hypothesis_id: h.lifecycle for h in v2.hypotheses}[
        h2.hypothesis_id] is ClaimLifecycle.SUPERSEDED


def test_mark_stale_and_revalidation_required():
    use_case, repo = _use_case()
    h1, h2 = _hypothesis(), _hypothesis()
    diag = _diagnostic(hypotheses=[h1, h2])
    repo.seed(diag)
    v1 = run(use_case.mark_hypothesis_stale_evidence(
        diagnostic_id=diag.diagnostic_id, hypothesis_id=h1.hypothesis_id,
    ))
    assert {h.hypothesis_id: h.effective_validation for h in v1.hypotheses}[
        h1.hypothesis_id] is EffectiveValidation.STALE_EVIDENCE
    v2 = run(use_case.mark_hypothesis_revalidation_required(
        diagnostic_id=diag.diagnostic_id, hypothesis_id=h2.hypothesis_id,
    ))
    assert {h.hypothesis_id: h.effective_validation for h in v2.hypotheses}[
        h2.hypothesis_id] is EffectiveValidation.REVALIDATION_REQUIRED


def test_validate_conclusion_postcondition():
    use_case, repo = _use_case()
    hyp = Hypothesis(
        "h-1", "causa", lifecycle=ClaimLifecycle.VALIDATED,
    )
    concl = DiagnosticConclusion(
        "c-1", "raiz", hypothesis_ids=("h-1",),
        root_cause=RootCauseDesignation("h-1"),
    )
    diag = _diagnostic(hypotheses=[hyp], diagnostic_conclusions=[concl])
    repo.seed(diag)
    view = run(use_case.validate_conclusion(
        diagnostic_id=diag.diagnostic_id, conclusion_id="c-1",
    ))
    persisted = view.diagnostic_conclusions[0]
    assert persisted.lifecycle is ClaimLifecycle.VALIDATED
    assert persisted.effective_validation is EffectiveValidation.CURRENT


def test_reject_and_supersede_conclusion():
    use_case, repo = _use_case()
    c1 = DiagnosticConclusion("c-1", "a")
    c2 = DiagnosticConclusion(
        "c-2", "b", lifecycle=ClaimLifecycle.VALIDATED,
    )
    diag = _diagnostic(diagnostic_conclusions=[c1, c2])
    repo.seed(diag)
    v1 = run(use_case.reject_conclusion(
        diagnostic_id=diag.diagnostic_id, conclusion_id="c-1",
    ))
    assert {c.conclusion_id: c.lifecycle for c in v1.diagnostic_conclusions}[
        "c-1"] is ClaimLifecycle.REJECTED
    v2 = run(use_case.supersede_conclusion(
        diagnostic_id=diag.diagnostic_id, conclusion_id="c-2",
    ))
    assert {c.conclusion_id: c.lifecycle for c in v2.diagnostic_conclusions}[
        "c-2"] is ClaimLifecycle.SUPERSEDED


def test_domain_rule_violation_maps_and_does_not_save():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.validate_hypothesis(
            diagnostic_id=diag.diagnostic_id,
            hypothesis_id="inexistente",
        ))
    assert _code(excinfo) == "invalid_causal_link"
    repo.save.assert_not_called()


# ---------------------------------------------------------------------------
# concurrency + read-back verification
# ---------------------------------------------------------------------------


def test_concurrent_modification_maps_to_stable_code():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)

    def drifted_save(d, *, expected_version):
        err = RuntimeError("lost update")
        err.code = "diagnostic.concurrent_modification"
        raise err

    repo.save = MagicMock(side_effect=drifted_save)
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.add_finding(
            diagnostic_id=diag.diagnostic_id,
            finding=Finding("f-1", "s"),
        ))
    assert _code(excinfo) == "diagnostic.concurrent_modification"


def test_save_success_but_divergent_readback_fails():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)

    original_get = repo.get

    def stale_get(diagnostic_id):
        # Save "succeeded" but read-back shows the unmutated aggregate —
        # rebuild an untouched Diagnostic to simulate divergent state.
        d = original_get(diagnostic_id)
        return Diagnostic(
            diagnostic_id=d.diagnostic_id,
            revision_id=d.revision_id,
            problem_statement=d.problem_statement,
            version=d.version + 1,
        )

    repo.get = stale_get  # type: ignore[assignment]
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(use_case.add_finding(
            diagnostic_id=diag.diagnostic_id,
            finding=Finding("f-1", "s"),
        ))
    assert _code(excinfo) == "diagnostic.outcome_verification_failed"


def test_returned_view_is_detached_snapshot():
    use_case, repo = _use_case()
    diag = _diagnostic()
    repo.seed(diag)
    view = run(use_case.add_finding(
        diagnostic_id=diag.diagnostic_id,
        finding=Finding("f-1", "s"),
    ))
    # Later aggregate mutation must not alias into the returned view.
    diag.add_hypothesis(_hypothesis())
    assert len(view.hypotheses) == 0
    assert not hasattr(view, "validate_hypothesis")
    assert isinstance(view.findings, tuple)
