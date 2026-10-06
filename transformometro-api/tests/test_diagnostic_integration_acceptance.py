"""Diagnostic V1 — Prompt 7 integration & acceptance tests.

Real-DB evidence: canonical migrations (V050/V051) applied to the real
plugins PostgreSQL; repositories are the production classes with an
injected test connection (``PluginBaseRepository`` connection seam).

Set ``TM_TEST_DSN`` to enable; the suite skips cleanly without it.
"""

from __future__ import annotations

import asyncio
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from starlette.requests import Request

psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row  # noqa: E402

from delpi_auth.request_context import (  # noqa: E402
    clear_current_user,
    clear_request_authorization,
    set_current_user,
    set_request_authorization,
)

from tm_app.application.governed_writes.errors import (  # noqa: E402
    PROPOSAL_ACTOR_MISMATCH,
    PROPOSAL_STALE,
    GovernedWriteError,
)
from tm_app.application.governed_writes.orchestrator import (  # noqa: E402
    GovernedWriteOrchestrator,
)
from tm_app.application.governed_writes.proposal_store import (  # noqa: E402
    get_proposal_store,
)
from tm_app.application.governed_writes.diagnostic_capabilities import (  # noqa: E402
    DiagnosticWriteStack,
)
from tm_app.application.security.transformometro_permissions import (  # noqa: E402
    ACCESS_PERMISSION,
)
from tm_app.application.use_cases.diagnostic_read import (  # noqa: E402
    GetDiagnostic,
    ListDiagnosticsByRevision,
)
from tm_app.application.use_cases.diagnostic_write import (  # noqa: E402
    DiagnosticWriteError,
    DiagnosticWriteUseCase,
)
from tm_app.domain.diagnostic.diagnostic import (  # noqa: E402
    CausalLink,
    ClaimLifecycle,
    DiagnosticConclusion,
    EffectiveValidation,
    EpistemicState,
    EvidenceLink,
    EvidenceRelation,
    Finding,
    Hypothesis,
    Provenance,
    ProvenanceOrigin,
    RootCauseDesignation,
)
from tm_app.infrastructure.persistence.repositories.diagnostic_readers import (  # noqa: E402
    EvidenceReaderAdapter,
    RevisionReaderAdapter,
)
from tm_app.infrastructure.persistence.repositories.diagnostic_repository import (  # noqa: E402
    DiagnosticRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_evidence_repository import (  # noqa: E402
    RevisaoEvidenceRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (  # noqa: E402
    RevisaoRepository,
)
from tm_app.infrastructure.security.diagnostic_authorization import (  # noqa: E402
    FreshAuthorizationAdapter,
)

_DSN = os.getenv("TM_TEST_DSN", "").strip()

_USER_ID = "user-acceptance-1"


@pytest.fixture(autouse=True)
def _reset_auth_context():
    """Contextvars are process-global - clear after each test."""
    yield
    clear_current_user()
    clear_request_authorization()


@pytest.fixture(scope="module")
def db():
    if not _DSN:
        pytest.skip("TM_TEST_DSN ausente — acceptance requer PG real.")
    conn = psycopg.connect(_DSN, row_factory=dict_row, autocommit=False)
    yield conn
    conn.close()


@pytest.fixture()
def anchors(db):
    """Context anchors: processo → revisao + 2 evidencias, cleanup after."""
    processo_id = str(uuid4())
    revisao_id = str(uuid4())
    evidencias = [str(uuid4()) for _ in range(2)]
    created: list[str] = []
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.processos
               (processo_id, codigo_processo, nome_processo)
               VALUES (%s, %s, %s)""",
            (processo_id, f"ACC-{processo_id[:8]}", "Processo aceite"),
        )
        cur.execute(
            """INSERT INTO transformometro.revisoes
               (revisao_id, processo_id, versao_revisao,
                chave_unica_processo_revisao, cenario_tipo,
                data_inicio_vigencia)
               VALUES (%s, %s, 'vA', %s, 'as_is', '2026-01-01')""",
            (revisao_id, processo_id, f"acc-key-{processo_id[:8]}"),
        )
        for evidencia_id in evidencias:
            cur.execute(
                """INSERT INTO transformometro.revisao_evidencias
                   (evidencia_id, revisao_id, tipo, nome_arquivo)
                   VALUES (%s, %s, 'anexo', %s)""",
                (evidencia_id, revisao_id, f"{evidencia_id[:8]}.pdf"),
            )
    db.commit()
    yield {
        "revisao_id": revisao_id,
        "evidencias": evidencias,
        "created": created,
    }
    with db.cursor() as cur:
        for did in created:
            cur.execute(
                "DELETE FROM transformometro.diagnostic_claim_snapshots"
                " WHERE diagnostic_id = %s",
                (did,),
            )
            cur.execute(
                "DELETE FROM transformometro.diagnostic_conclusion_refs r"
                " USING transformometro.diagnostic_conclusions c"
                " WHERE r.conclusion_id = c.conclusion_id"
                "   AND c.diagnostic_id = %s",
                (did,),
            )
            for table in (
                "diagnostic_conclusions",
                "diagnostic_evidence_links",
                "diagnostic_causal_links",
                "diagnostic_hypotheses",
                "diagnostic_findings",
            ):
                cur.execute(
                    f"DELETE FROM transformometro.{table}"
                    " WHERE diagnostic_id = %s",
                    (did,),
                )
            cur.execute(
                "DELETE FROM transformometro.diagnostics"
                " WHERE diagnostic_id = %s",
                (did,),
            )
        for evidencia_id in evidencias:
            cur.execute(
                "DELETE FROM transformometro.revisao_evidencias"
                " WHERE evidencia_id = %s",
                (evidencia_id,),
            )
        cur.execute(
            "DELETE FROM transformometro.revisoes WHERE revisao_id = %s",
            (revisao_id,),
        )
        cur.execute(
            "DELETE FROM transformometro.processos WHERE processo_id = %s",
            (processo_id,),
        )
    db.commit()


def _repos(db):
    diagnostics = DiagnosticRepository(db)
    revisions = RevisionReaderAdapter(RevisaoRepository(db))
    evidence = EvidenceReaderAdapter(RevisaoEvidenceRepository(db))
    return diagnostics, revisions, evidence


def _use_case(db) -> DiagnosticWriteUseCase:
    diagnostics, revisions, evidence = _repos(db)
    return DiagnosticWriteUseCase(
        diagnostics=diagnostics,
        revisions=revisions,
        evidence=evidence,
        authorization=FreshAuthorizationAdapter(),
    )


def _stack(db) -> DiagnosticWriteStack:
    diagnostics, revisions, evidence = _repos(db)
    return DiagnosticWriteStack(
        use_case=_use_case(db),
        diagnostics=diagnostics,
        revisions=revisions,
        evidence=evidence,
    )


@pytest.fixture()
def rbac(monkeypatch):
    """Controlled fresh Core answers — proves fresh lookup is consulted."""
    calls: list[bool] = []
    state = {
        "permissions": [ACCESS_PERMISSION],
        "is_superadmin": False,
        "fail": None,
    }

    async def fake_load_user_rbac(token, force_refresh=False):
        calls.append(force_refresh)
        if state["fail"] is not None:
            raise state["fail"]
        return {
            "permissions": list(state["permissions"]),
            "is_superadmin": state["is_superadmin"],
        }

    monkeypatch.setattr(
        "tm_app.infrastructure.security.diagnostic_authorization.load_user_rbac",
        fake_load_user_rbac,
    )
    state["calls"] = calls
    yield state


def _request(user_id: str = _USER_ID) -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/",
            "headers": [],
            "state": {},
        }
    )


def _prime_ctx(user_id: str = _USER_ID):
    user = SimpleNamespace(
        id=user_id,
        email=f"{user_id}@delpi.test",
        principal_type="user",
        permissions=[ACCESS_PERMISSION],
        is_superadmin=False,
        access_token="tok-acceptance",
    )
    set_current_user(user)
    set_request_authorization("Bearer tok-acceptance")


def _request_with_user(user_id: str = _USER_ID) -> Request:
    req = _request()
    req.state.user = SimpleNamespace(
        id=user_id,
        email=user_id + "@delpi.test",
        principal_type="user",
        permissions=[ACCESS_PERMISSION],
        is_superadmin=False,
    )
    return req


def _code(excinfo) -> str:
    return excinfo.value.code


def _count(db, table: str, diagnostic_id: str) -> int:
    with db.cursor() as cur:
        cur.execute(
            f"SELECT COUNT(*) AS n FROM transformometro.{table}"
            " WHERE diagnostic_id = %s",
            (diagnostic_id,),
        )
        return cur.fetchone()["n"]


# ---------------------------------------------------------------------------
# §6 Persistence-real integrated scenario
# ---------------------------------------------------------------------------


def test_real_db_full_diagnostic_lifecycle(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    rev = anchors["revisao_id"]

    view = asyncio.run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=rev,
            problem_statement="gargalo no processo",
            provenance=Provenance(origin=ProvenanceOrigin.USER),
        )
    )
    db.commit()
    assert view.diagnostic_id == did and view.version == 1

    run = asyncio.run
    run(uc.add_finding(diagnostic_id=did, finding=Finding("f1f1f1f1-0000-4000-8000-000000000001", "fila no aprovacao")))
    run(
        uc.add_hypothesis(
            diagnostic_id=did,
            hypothesis=Hypothesis("a1a1a1a1-0000-4000-8000-000000000001", "falta de automacao"),
        )
    )
    run(
        uc.validate_hypothesis(
            diagnostic_id=did, hypothesis_id="a1a1a1a1-0000-4000-8000-000000000001", note="evidenciado"
        )
    )
    run(
        uc.add_evidence_link(
            diagnostic_id=did,
            link=EvidenceLink(
                "e1e1e1e1-0000-4000-8000-000000000001",
                evidence_id=anchors["evidencias"][0],
                relation=EvidenceRelation.SUPPORTS,
                target_id="a1a1a1a1-0000-4000-8000-000000000001",
            ),
        )
    )
    # Conclusion with root cause → validate → durable reload.
    _H = "a1a1a1a1-0000-4000-8000-000000000001"
    _C = "c1c1c1c1-0000-4000-8000-000000000001"
    conclusion = DiagnosticConclusion(
        _C,
        "causa raiz identificada",
        hypothesis_ids=(_H,),
        root_cause=RootCauseDesignation(_H),
    )
    run(uc.add_conclusion(diagnostic_id=did, conclusion=conclusion))
    run(uc.validate_conclusion(diagnostic_id=did, conclusion_id=_C, note="ok"))
    db.commit()

    repo, _, _ = _repos(db)
    reloaded = repo.get(did)
    assert reloaded.version == 7
    assert len(reloaded.findings) == 1
    hypo = next(h for h in reloaded.hypotheses if h.hypothesis_id == _H)
    assert hypo.lifecycle is ClaimLifecycle.VALIDATED
    assert hypo.epistemic_state is EpistemicState.INFERRED
    assert len(reloaded.evidence_links) == 1
    concl = next(
        c for c in reloaded.diagnostic_conclusions if c.conclusion_id == _C
    )
    assert concl.lifecycle is ClaimLifecycle.VALIDATED
    assert concl.epistemic_state is EpistemicState.INFERRED
    assert concl.effective_validation is EffectiveValidation.CURRENT
    assert concl.root_cause is not None
    assert concl.root_cause.hypothesis_id == _H
    # validation history preserved through reload
    assert any(
        s.to_lifecycle is ClaimLifecycle.VALIDATED
        for s in hypo.validation_history
    )
    assert any(
        s.to_lifecycle is ClaimLifecycle.VALIDATED
        for s in concl.validation_history
    )


# ---------------------------------------------------------------------------
# §7 Evidence integration — real readers
# ---------------------------------------------------------------------------


def test_evidence_same_revision_persists_and_read_back(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    run(
        uc.add_hypothesis(
            diagnostic_id=did,
            hypothesis=Hypothesis("a1a1a1a1-0000-4000-8000-000000000001", "h"),
        )
    )
    link = EvidenceLink(
        "e1e1e1e1-0000-4000-8000-000000000001",
        evidence_id=anchors["evidencias"][0],
        relation=EvidenceRelation.SUPPORTS,
        target_id="a1a1a1a1-0000-4000-8000-000000000001",
    )
    view = run(uc.add_evidence_link(diagnostic_id=did, link=link))
    db.commit()
    assert any(
        l.evidence_id == anchors["evidencias"][0] for l in view.evidence_links
    )


def test_evidence_foreign_revision_rejected_no_save(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    run(
        uc.add_hypothesis(
            diagnostic_id=did,
            hypothesis=Hypothesis("a1a1a1a1-0000-4000-8000-000000000001", "h"),
        )
    )
    link = EvidenceLink(
        "e2e2e2e2-0000-4000-8000-00000000000a",
        evidence_id=str(uuid4()),
        relation=EvidenceRelation.SUPPORTS,
        target_id="a1a1a1a1-0000-4000-8000-000000000001",
    )
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(uc.add_evidence_link(diagnostic_id=did, link=link))
    assert excinfo.value.code == "diagnostic.evidence_out_of_revision"
    db.commit()
    assert _count(db, "diagnostic_evidence_links", did) == 0


# ---------------------------------------------------------------------------
# §8 Governed PREPARE→ACT — real persistence
# ---------------------------------------------------------------------------


def test_governed_prepare_act_create_manage_real_db(db, anchors, rbac):
    _prime_ctx()
    orch = GovernedWriteOrchestrator(diagnostic_stack=_stack(db))
    did = str(uuid4())
    anchors["created"].append(did)
    req = _request_with_user()

    # PREPARE create — zero persistence
    prepared = orch.prepare(
        req,
        capability="create_diagnostic",
        args={
            "diagnostic_id": did,
            "revision_id": anchors["revisao_id"],
            "problem_statement": "problema governado",
            "provenance": {"origin": "USER"},
        },
    )
    assert prepared["proposal_handle"]
    assert _count(db, "diagnostics", did) == 0  # PREPARE persisted nothing

    result = orch.act(
        req,
        capability="create_diagnostic",
        proposal_handle=prepared["proposal_handle"],
    )
    assert result["verified"] is True
    db.commit()
    repo, _, _ = _repos(db)
    persisted = repo.get(did)
    assert persisted is not None and persisted.version == 1

    # Single-use: replay must be denied
    with pytest.raises(GovernedWriteError):
        orch.act(
            req,
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )

    # manage/add_hypothesis through the same governed path
    prepared_h = orch.prepare(
        req,
        capability="manage_diagnostic",
        args={
            "diagnostic_id": did,
            "action": "add_hypothesis",
            "payload": {"hypothesis_id": "b1b1b1b1-0000-4000-8000-000000000001", "statement": "via governed"},
        },
    )
    result_h = orch.act(
        req,
        capability="manage_diagnostic",
        proposal_handle=prepared_h["proposal_handle"],
    )
    assert result_h["verified"] is True
    db.commit()
    reloaded = repo.get(did)
    assert any(h.hypothesis_id == "b1b1b1b1-0000-4000-8000-000000000001" for h in reloaded.hypotheses)
    assert reloaded.version == 2

    # validate_hypothesis governed — lifecycle postcondition
    prepared_v = orch.prepare(
        req,
        capability="manage_diagnostic",
        args={
            "diagnostic_id": did,
            "action": "validate_hypothesis",
            "payload": {"hypothesis_id": "b1b1b1b1-0000-4000-8000-000000000001", "note": "ok"},
        },
    )
    result_v = orch.act(
        req,
        capability="manage_diagnostic",
        proposal_handle=prepared_v["proposal_handle"],
    )
    assert result_v["verified"] is True
    hypo = result_v["data"]["diagnostic"]["hypotheses"][0]
    assert hypo["lifecycle"] == "VALIDATED"
    assert rbac["calls"] and all(c is True for c in rbac["calls"])


# ---------------------------------------------------------------------------
# §10 Actor binding — real proposal store
# ---------------------------------------------------------------------------


def test_actor_mismatch_denied_real_db(db, anchors, rbac):
    _prime_ctx()
    orch = GovernedWriteOrchestrator(diagnostic_stack=_stack(db))
    did = str(uuid4())
    anchors["created"].append(did)

    prepared = orch.prepare(
        _request_with_user("actor-A"),
        capability="create_diagnostic",
        args={
            "diagnostic_id": did,
            "revision_id": anchors["revisao_id"],
            "problem_statement": "p",
        },
    )
    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            _request_with_user("actor-B"),
            capability="create_diagnostic",
            proposal_handle=prepared["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_ACTOR_MISMATCH
    assert _count(db, "diagnostics", did) == 0


# ---------------------------------------------------------------------------
# §12 Stale proposal — legitimate mutation between PREPARE and ACT
# ---------------------------------------------------------------------------


def test_stale_proposal_after_legitimate_mutation(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    orch = GovernedWriteOrchestrator(diagnostic_stack=_stack(db))
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    req = _request_with_user()

    prepared_c = orch.prepare(
        req,
        capability="create_diagnostic",
        args={
            "diagnostic_id": did,
            "revision_id": anchors["revisao_id"],
            "problem_statement": "p",
        },
    )
    orch.act(
        req,
        capability="create_diagnostic",
        proposal_handle=prepared_c["proposal_handle"],
    )
    db.commit()

    prepared_h = orch.prepare(
        req,
        capability="manage_diagnostic",
        args={
            "diagnostic_id": did,
            "action": "add_hypothesis",
            "payload": {"hypothesis_id": "c1c1c1c1-0000-4000-8000-000000000001", "statement": "s"},
        },
    )
    # Legitimate write between PREPARE and ACT bumps the aggregate.
    run(
        uc.add_finding(
            diagnostic_id=did,
            finding=Finding("f2f2f2f2-0000-4000-8000-000000000002", "mutacao legitima"),
        )
    )
    db.commit()

    with pytest.raises(GovernedWriteError) as excinfo:
        orch.act(
            req,
            capability="manage_diagnostic",
            proposal_handle=prepared_h["proposal_handle"],
        )
    assert _code(excinfo) == PROPOSAL_STALE
    db.commit()
    repo, _, _ = _repos(db)
    reloaded = repo.get(did)
    assert not any(h.hypothesis_id == "c1c1c1c1-0000-4000-8000-000000000001" for h in reloaded.hypotheses)
    assert len(reloaded.hypotheses) == 0


# ---------------------------------------------------------------------------
# §14 Domain negatives — authorized user, illegal domain mutation
# ---------------------------------------------------------------------------


def test_domain_negative_authorized_user_state_unchanged(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    db.commit()

    # Invalid lifecycle transition: VALIDATED cannot go straight to SUPERSEDED
    # from DRAFT — supersede requires VALIDATED lifecycle.
    run(
        uc.add_hypothesis(
            diagnostic_id=did,
            hypothesis=Hypothesis("a1a1a1a1-0000-4000-8000-000000000001", "h"),
        )
    )
    db.commit()
    with pytest.raises(DiagnosticWriteError):
        run(
            uc.supersede_hypothesis(
                diagnostic_id=did, hypothesis_id="a1a1a1a1-0000-4000-8000-000000000001"
            )
        )
    db.commit()
    repo, _, _ = _repos(db)
    reloaded = repo.get(did)
    hypo = next(h for h in reloaded.hypotheses if h.hypothesis_id == "a1a1a1a1-0000-4000-8000-000000000001")
    assert hypo.lifecycle is ClaimLifecycle.DRAFT


def test_validate_missing_hypothesis_denied(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    db.commit()
    with pytest.raises(DiagnosticWriteError):
        run(
            uc.validate_hypothesis(
                diagnostic_id=did, hypothesis_id="d4d4d4d4-0000-4000-8000-000000000004"
            )
        )
    db.commit()
    repo, _, _ = _repos(db)
    assert repo.get(did).version == 1


# ---------------------------------------------------------------------------
# §16 Read side — real persisted data, detached views, no side effects
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# GAP B — invalid root cause: authorized user, domain rejection, durable proof
# ---------------------------------------------------------------------------


def test_root_cause_unvalidated_hypothesis_rejected(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    _H = "a1a1a1a1-0000-4000-8000-000000000001"
    _C = "c1c1c1c1-0000-4000-8000-000000000001"
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    run(
        uc.add_hypothesis(
            diagnostic_id=did,
            hypothesis=Hypothesis(_H, "h draft — nunca validada"),
        )
    )
    run(
        uc.add_conclusion(
            diagnostic_id=did,
            conclusion=DiagnosticConclusion(
                _C,
                "conclusao com root cause nao validada",
                hypothesis_ids=(_H,),
                root_cause=RootCauseDesignation(_H),
            ),
        )
    )
    db.commit()
    repo, _, _ = _repos(db)
    version_before = repo.get(did).version

    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(uc.validate_conclusion(diagnostic_id=did, conclusion_id=_C))
    assert excinfo.value.code == "invalid_root_cause_designation"
    db.commit()

    reloaded = repo.get(did)
    assert reloaded.version == version_before
    concl = next(
        c for c in reloaded.diagnostic_conclusions if c.conclusion_id == _C
    )
    assert concl.lifecycle is ClaimLifecycle.DRAFT
    assert not any(
        c.lifecycle is ClaimLifecycle.VALIDATED
        for c in reloaded.diagnostic_conclusions
    )


# ---------------------------------------------------------------------------
# GAP C — second VALIDATED conclusion
# ---------------------------------------------------------------------------


def test_second_validated_conclusion_rejected(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    _H = "a1a1a1a1-0000-4000-8000-000000000001"
    _C1 = "c1c1c1c1-0000-4000-8000-000000000001"
    _C2 = "c2c2c2c2-0000-4000-8000-000000000002"
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    run(
        uc.add_hypothesis(
            diagnostic_id=did, hypothesis=Hypothesis(_H, "h")
        )
    )
    run(uc.validate_hypothesis(diagnostic_id=did, hypothesis_id=_H))
    run(
        uc.add_conclusion(
            diagnostic_id=did,
            conclusion=DiagnosticConclusion(
                _C1,
                "primeira",
                hypothesis_ids=(_H,),
                root_cause=RootCauseDesignation(_H),
            ),
        )
    )
    run(uc.validate_conclusion(diagnostic_id=did, conclusion_id=_C1))
    run(
        uc.add_conclusion(
            diagnostic_id=did,
            conclusion=DiagnosticConclusion(_C2, "segunda"),
        )
    )
    db.commit()
    repo, _, _ = _repos(db)
    version_before = repo.get(did).version

    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(uc.validate_conclusion(diagnostic_id=did, conclusion_id=_C2))
    assert excinfo.value.code == "effective_conclusion_conflict"
    db.commit()

    reloaded = repo.get(did)
    assert reloaded.version == version_before
    by_id = {c.conclusion_id: c for c in reloaded.diagnostic_conclusions}
    assert by_id[_C1].lifecycle is ClaimLifecycle.VALIDATED
    assert by_id[_C2].lifecycle is ClaimLifecycle.DRAFT
    assert sum(
        c.lifecycle is ClaimLifecycle.VALIDATED
        for c in reloaded.diagnostic_conclusions
    ) == 1


# ---------------------------------------------------------------------------
# GAP D — invalid causal reference
# ---------------------------------------------------------------------------


def test_invalid_causal_reference_rejected(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    _F = "f1f1f1f1-0000-4000-8000-000000000001"
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="p",
        )
    )
    run(
        uc.add_finding(
            diagnostic_id=did, finding=Finding(_F, "achado")
        )
    )
    db.commit()
    repo, _, _ = _repos(db)
    version_before = repo.get(did).version

    link = CausalLink(
        "caca1111-0000-4000-8000-000000000001",
        source_hypothesis_id=str(uuid4()),  # hypothesis inexistente
        target_id=_F,
    )
    with pytest.raises(DiagnosticWriteError) as excinfo:
        run(uc.add_causal_link(diagnostic_id=did, link=link))
    assert excinfo.value.code == "invalid_causal_link"
    db.commit()

    reloaded = repo.get(did)
    assert reloaded.version == version_before
    assert len(reloaded.causal_links) == 0
    assert len(reloaded.findings) == 1


# ---------------------------------------------------------------------------
# §8 — confirmation policy deny-by-default for Diagnostic capabilities
# ---------------------------------------------------------------------------


def test_diagnostic_commit_now_deny_by_default():
    """Canonical execution policy for Diagnostic capabilities.

    create_diagnostic is a pure additive root entity -> auto_act
    (the Actions commit_now mechanism may implement it, though
    diagnostic writes remain MCP-native today). manage_diagnostic
    includes lifecycle supersession -> confirm_before_act.
    """
    from tm_app.application.governed_writes.confirmation_policy import (
        AUTO_ACT,
        CONFIRM_BEFORE_ACT,
        allows_commit_now_for_capability,
        execution_policy_for_capability,
    )

    assert execution_policy_for_capability("create_diagnostic") == AUTO_ACT
    assert (
        execution_policy_for_capability("manage_diagnostic")
        == CONFIRM_BEFORE_ACT
    )
    assert allows_commit_now_for_capability("create_diagnostic") is True
    assert allows_commit_now_for_capability("manage_diagnostic") is False


def test_read_side_detached_and_no_writes(db, anchors, rbac):
    _prime_ctx()
    uc = _use_case(db)
    did = str(uuid4())
    anchors["created"].append(did)
    run = asyncio.run
    run(
        uc.create_diagnostic(
            diagnostic_id=did,
            revision_id=anchors["revisao_id"],
            problem_statement="leitura",
        )
    )
    db.commit()
    repo, _, _ = _repos(db)

    repo2, revisions, evidence = _repos(db)
    ctx = GetDiagnostic(repo2, revisions, evidence).execute(did)
    view = ctx.diagnostic
    assert view.diagnostic_id == did
    # Mutating the aggregate afterwards must not alter the detached view.
    run(
        uc.add_finding(
            diagnostic_id=did,
            finding=Finding("f3f3f3f3-0000-4000-8000-000000000003", "novo"),
        )
    )
    db.commit()
    assert view.findings == ()  # detached snapshot, no aliasing

    listed = ListDiagnosticsByRevision(repo, revisions).execute(
        anchors["revisao_id"]
    )
    items = list(listed.items)
    assert [d.diagnostic_id for d in items] == sorted(
        d.diagnostic_id for d in items
    )
    assert any(d.diagnostic_id == did for d in items)
