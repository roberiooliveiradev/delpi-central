"""Diagnostic V1 — PostgreSQL persistence tests.

Runs against a real PostgreSQL with the transformometro migrations applied.
Set ``TM_TEST_DSN`` (psycopg conninfo) to enable; the suite skips cleanly in
environments without a reachable test database — same policy used for
integration suites that need live infrastructure.
"""

from __future__ import annotations

import os
from uuid import uuid4

import pytest

psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row  # noqa: E402

from tm_app.domain.diagnostic.diagnostic import (  # noqa: E402
    CausalLink,
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    DiagnosticError,
    EffectiveValidation,
    EpistemicState,
    EvidenceLink,
    EvidenceRelation,
    Finding,
    FindingRole,
    Hypothesis,
    ProblemStatement,
    Provenance,
    ProvenanceOrigin,
    RootCauseDesignation,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (  # noqa: E402
    PluginsRepositoryError,
)
from tm_app.infrastructure.persistence.repositories.diagnostic_repository import (  # noqa: E402
    DiagnosticConcurrencyError,
    DiagnosticFidelityError,
    DiagnosticRepository,
)

_DSN = os.getenv("TM_TEST_DSN", "").strip()


def _connect():
    return psycopg.connect(_DSN, row_factory=dict_row, autocommit=False)


@pytest.fixture(scope="module")
def db():
    if not _DSN:
        pytest.skip("TM_TEST_DSN ausente — persistence tests requerem PG real.")
    try:
        conn = _connect()
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"Postgres de teste indisponível: {exc}")
    yield conn
    conn.close()


@pytest.fixture()
def fixture_ids(db):
    """Minimal contextual anchors: processo → revisao → evidencias."""
    processo_id = str(uuid4())
    revisao_id = str(uuid4())
    evidencias = [str(uuid4()) for _ in range(3)]
    created_diagnostics: list[str] = []
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.processos
               (processo_id, codigo_processo, nome_processo)
               VALUES (%s, %s, %s)""",
            (processo_id, f"TST-{processo_id[:8]}", "Processo teste"),
        )
        cur.execute(
            """INSERT INTO transformometro.revisoes
               (revisao_id, processo_id, versao_revisao,
                chave_unica_processo_revisao, cenario_tipo,
                data_inicio_vigencia)
               VALUES (%s, %s, 'vT', %s, 'as_is', '2026-01-01')""",
            (revisao_id, processo_id, f"key-{processo_id[:8]}"),
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
        "processo_id": processo_id,
        "revisao_id": revisao_id,
        "evidencias": evidencias,
        "created_diagnostics": created_diagnostics,
    }
    with db.cursor() as cur:
        for did in created_diagnostics:
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


@pytest.fixture()
def repo(db):
    return DiagnosticRepository(connection=db)


def _uid() -> str:
    return str(uuid4())


def _prov_user() -> Provenance:
    return Provenance(origin=ProvenanceOrigin.USER, detail="analista")


def _prov_teo() -> Provenance:
    return Provenance(origin=ProvenanceOrigin.TEO, detail="teo-run-1")


def _complex_diagnostic(revisao_id: str, evidencias: list[str]) -> Diagnostic:
    """Aggregate covering every persistence dimension of the kernel."""
    f_observed = Finding(
        finding_id=_uid(),
        statement="falha observada no gargalo",
        epistemic_state=EpistemicState.OBSERVED,
        role=FindingRole.SYMPTOM,
        provenance=_prov_user(),
    )
    f_calculated = Finding(
        finding_id=_uid(),
        statement="retrabalho calculado em 12%",
        epistemic_state=EpistemicState.CALCULATED,
        provenance=_prov_teo(),
    )
    h1 = Hypothesis(
        hypothesis_id=_uid(),
        statement="capacidade insuficiente",
        provenance=_prov_user(),
    )
    h2 = Hypothesis(
        hypothesis_id=_uid(),
        statement="layout gera deslocamento extra",
        provenance=_prov_teo(),
    )
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=revisao_id,
        problem_statement=ProblemStatement("perda de capacidade na linha A"),
        findings=[f_observed, f_calculated],
        hypotheses=[h1, h2],
        provenance=_prov_user(),
    )
    diagnostic.validate_hypothesis(h1.hypothesis_id, note="evidência forte")
    diagnostic.mark_hypothesis_stale_evidence(h2.hypothesis_id)

    diagnostic.add_causal_link(
        CausalLink(
            link_id=_uid(),
            source_hypothesis_id=h1.hypothesis_id,
            target_id=f_observed.finding_id,
        )
    )
    diagnostic.add_causal_link(
        CausalLink(
            link_id=_uid(),
            source_hypothesis_id=h1.hypothesis_id,
            target_id=h2.hypothesis_id,
        )
    )
    diagnostic.add_evidence_link(
        EvidenceLink(
            link_id=_uid(),
            evidence_id=evidencias[0],
            relation=EvidenceRelation.SUPPORTS,
            target_id=h1.hypothesis_id,
        )
    )
    diagnostic.add_evidence_link(
        EvidenceLink(
            link_id=_uid(),
            evidence_id=evidencias[1],
            relation=EvidenceRelation.CONTRADICTS,
            target_id=h2.hypothesis_id,
        )
    )
    diagnostic.add_evidence_link(
        EvidenceLink(
            link_id=_uid(),
            evidence_id=evidencias[2],
            relation=EvidenceRelation.CONTEXTUALIZES,
        )
    )
    diagnostic.add_conclusion(
        DiagnosticConclusion(
            conclusion_id=_uid(),
            statement="conclusão em análise",
            hypothesis_ids=(h2.hypothesis_id,),
            finding_ids=(f_observed.finding_id,),
            provenance=_prov_user(),
        )
    )
    diagnostic.add_conclusion(
        DiagnosticConclusion(
            conclusion_id=_uid(),
            statement="causa raiz confirmada",
            rationale="consenso do comitê",
            hypothesis_ids=(h1.hypothesis_id, h2.hypothesis_id),
            finding_ids=(f_observed.finding_id, f_calculated.finding_id),
            root_cause=RootCauseDesignation(h1.hypothesis_id),
            provenance=_prov_teo(),
        )
    )
    return diagnostic


def _find(tpl, key, value):
    return next(x for x in tpl if getattr(x, key) == value)


def _assert_same_aggregate(a: Diagnostic, b: Diagnostic) -> None:
    assert a.diagnostic_id == b.diagnostic_id
    assert a.revision_id == b.revision_id
    assert a.problem_statement.text == b.problem_statement.text
    assert a.version == b.version
    assert a.provenance == b.provenance

    assert {f.finding_id for f in a.findings} == {
        f.finding_id for f in b.findings
    }
    for f in a.findings:
        other = _find(b.findings, "finding_id", f.finding_id)
        assert other == f

    assert {h.hypothesis_id for h in a.hypotheses} == {
        h.hypothesis_id for h in b.hypotheses
    }
    for h in a.hypotheses:
        other = _find(b.hypotheses, "hypothesis_id", h.hypothesis_id)
        assert other == h

    assert sorted(
        (l.link_id, l.source_hypothesis_id, l.target_id)
        for l in a.causal_links
    ) == sorted(
        (l.link_id, l.source_hypothesis_id, l.target_id)
        for l in b.causal_links
    )
    assert sorted(
        (l.link_id, l.evidence_id, l.relation, l.target_id)
        for l in a.evidence_links
    ) == sorted(
        (l.link_id, l.evidence_id, l.relation, l.target_id)
        for l in b.evidence_links
    )

    assert {c.conclusion_id for c in a.diagnostic_conclusions} == {
        c.conclusion_id for c in b.diagnostic_conclusions
    }
    for c in a.diagnostic_conclusions:
        other = _find(b.diagnostic_conclusions, "conclusion_id",
                      c.conclusion_id)
        assert other == c


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_round_trip_full_aggregate(repo, db, fixture_ids):
    diagnostic = _complex_diagnostic(
        fixture_ids["revisao_id"], fixture_ids["evidencias"]
    )
    validated_c = _find(
        diagnostic.diagnostic_conclusions,
        "statement",
        "causa raiz confirmada",
    )
    diagnostic.validate_conclusion(
        validated_c.conclusion_id, note="aprovada"
    )

    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)
    loaded = repo.get(diagnostic.diagnostic_id)

    assert loaded is not None
    _assert_same_aggregate(diagnostic, loaded)

    # spot-checks on the deepest fields
    h1 = _find(
        loaded.hypotheses,
        "statement",
        "capacidade insuficiente",
    )
    assert h1.lifecycle is ClaimLifecycle.VALIDATED
    assert h1.effective_validation is EffectiveValidation.CURRENT
    assert len(h1.validation_history) == 1
    snap = h1.validation_history[0]
    assert snap.from_lifecycle is ClaimLifecycle.DRAFT
    assert snap.to_lifecycle is ClaimLifecycle.VALIDATED
    assert snap.note == "evidência forte"

    h2 = _find(loaded.hypotheses, "statement",
               "layout gera deslocamento extra")
    assert h2.lifecycle is ClaimLifecycle.DRAFT
    assert h2.effective_validation is EffectiveValidation.STALE_EVIDENCE

    vc = _find(loaded.diagnostic_conclusions, "statement",
               "causa raiz confirmada")
    assert vc.lifecycle is ClaimLifecycle.VALIDATED
    assert vc.root_cause is not None
    assert vc.root_cause.hypothesis_id == h1.hypothesis_id
    assert set(vc.hypothesis_ids) == {h1.hypothesis_id, h2.hypothesis_id}
    assert len(vc.validation_history) == 1
    assert vc.validation_history[0].to_lifecycle is ClaimLifecycle.VALIDATED


def test_list_by_revision(repo, db, fixture_ids):
    first = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("primeiro"),
    )
    second = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("segundo"),
    )
    fixture_ids["created_diagnostics"] += [
        first.diagnostic_id,
        second.diagnostic_id,
    ]
    repo.create(first)
    repo.create(second)

    loaded = repo.list_by_revision(fixture_ids["revisao_id"])
    assert {d.diagnostic_id for d in loaded} == {
        first.diagnostic_id,
        second.diagnostic_id,
    }


def test_get_missing_returns_none(repo, db, fixture_ids):
    assert repo.get(_uid()) is None


# ---------------------------------------------------------------------------
# Rehydration states
# ---------------------------------------------------------------------------


def test_rehydrate_all_lifecycle_states(repo, db, fixture_ids):
    h_validated = Hypothesis(
        hypothesis_id=_uid(), statement="v",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
    )
    h_rejected = Hypothesis(
        hypothesis_id=_uid(), statement="r",
        lifecycle=ClaimLifecycle.REJECTED,
    )
    h_superseded = Hypothesis(
        hypothesis_id=_uid(), statement="s",
        lifecycle=ClaimLifecycle.SUPERSEDED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
    )
    c_draft = DiagnosticConclusion(
        conclusion_id=_uid(), statement="draft",
        hypothesis_ids=(h_validated.hypothesis_id,),
        root_cause=RootCauseDesignation(h_validated.hypothesis_id),
    )
    c_validated = DiagnosticConclusion(
        conclusion_id=_uid(), statement="validated",
        lifecycle=ClaimLifecycle.VALIDATED,
        hypothesis_ids=(h_validated.hypothesis_id,),
        root_cause=RootCauseDesignation(h_validated.hypothesis_id),
    )
    c_rejected = DiagnosticConclusion(
        conclusion_id=_uid(), statement="rejected",
        lifecycle=ClaimLifecycle.REJECTED,
    )
    c_superseded = DiagnosticConclusion(
        conclusion_id=_uid(), statement="superseded",
        lifecycle=ClaimLifecycle.SUPERSEDED,
    )
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("estados históricos"),
        hypotheses=[h_validated, h_rejected, h_superseded],
        diagnostic_conclusions=[
            c_draft, c_validated, c_rejected, c_superseded,
        ],
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)
    loaded = repo.get(diagnostic.diagnostic_id)

    assert loaded is not None
    states = {h.hypothesis_id: h for h in loaded.hypotheses}
    assert states[h_validated.hypothesis_id].lifecycle is (
        ClaimLifecycle.VALIDATED
    )
    assert states[h_rejected.hypothesis_id].lifecycle is (
        ClaimLifecycle.REJECTED
    )
    assert states[h_superseded.hypothesis_id].effective_validation is (
        EffectiveValidation.STALE_EVIDENCE
    )
    c_states = {c.conclusion_id: c for c in loaded.diagnostic_conclusions}
    assert c_states[c_validated.conclusion_id].lifecycle is (
        ClaimLifecycle.VALIDATED
    )
    assert c_states[c_superseded.conclusion_id].lifecycle is (
        ClaimLifecycle.SUPERSEDED
    )
    assert c_states[c_validated.conclusion_id].root_cause is not None

    # read-only tuple views survive the round-trip
    assert isinstance(loaded.hypotheses, tuple)
    with pytest.raises(AttributeError):
        loaded.hypotheses.append(h_validated)


# ---------------------------------------------------------------------------
# Optimistic concurrency
# ---------------------------------------------------------------------------


def test_concurrent_modification_no_lost_update(repo, db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("base"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    a = repo.get(diagnostic.diagnostic_id)
    b = repo.get(diagnostic.diagnostic_id)
    assert a.version == b.version == 1

    a.add_finding(Finding(finding_id=_uid(), statement="ache A"))
    new_version = repo.save(a, expected_version=1)
    assert new_version == 2

    b.add_finding(Finding(finding_id=_uid(), statement="ache B"))
    with pytest.raises(DiagnosticConcurrencyError) as excinfo:
        repo.save(b, expected_version=1)
    assert excinfo.value.code == "diagnostic.concurrent_modification"
    db.rollback()

    authoritative = repo.get(diagnostic.diagnostic_id)
    assert authoritative.version == 2
    assert [f.statement for f in authoritative.findings] == ["ache A"]


# ---------------------------------------------------------------------------
# Transaction rollback
# ---------------------------------------------------------------------------


def test_failed_save_rolls_back_everything(repo, db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("rollback alvo"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)

    # FK failure mid-write: evidence link points to an evidence that does
    # not exist. The domain accepts it (cross-aggregate rule is deferred),
    # the DB must refuse — and nothing partial may survive.
    diagnostic.add_evidence_link(
        EvidenceLink(
            link_id=_uid(),
            evidence_id=_uid(),
            relation=EvidenceRelation.SUPPORTS,
        )
    )
    with pytest.raises(PluginsRepositoryError):
        repo.create(diagnostic)
    db.rollback()

    assert repo.get(diagnostic.diagnostic_id) is None
    with db.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS n FROM transformometro.diagnostic_evidence_links"
            " WHERE diagnostic_id = %s",
            (diagnostic.diagnostic_id,),
        )
        assert cur.fetchone()["n"] == 0


def test_failed_update_preserves_previous_state(repo, db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("estado anterior"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    loaded = repo.get(diagnostic.diagnostic_id)
    loaded.add_evidence_link(
        EvidenceLink(
            link_id=_uid(),
            evidence_id=_uid(),  # violates FK inside the same tx
            relation=EvidenceRelation.SUPPORTS,
        )
    )
    with pytest.raises(PluginsRepositoryError):
        repo.save(loaded, expected_version=1)
    db.rollback()

    authoritative = repo.get(diagnostic.diagnostic_id)
    assert authoritative.version == 1
    assert authoritative.evidence_links == ()


# ---------------------------------------------------------------------------
# DB constraints
# ---------------------------------------------------------------------------


def test_revision_fk_enforced(repo, db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=_uid(),  # revisão inexistente
        problem_statement=ProblemStatement("sem revisão"),
    )
    with pytest.raises(PluginsRepositoryError):
        repo.create(diagnostic)
    db.rollback()


def test_duplicate_stable_identity_rejected(repo, db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("dup"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    other = Diagnostic(
        diagnostic_id=diagnostic.diagnostic_id,
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("mesmo id"),
    )
    with pytest.raises(PluginsRepositoryError):
        repo.create(other)
    db.rollback()


def test_enum_checks_enforced(db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("enum"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    DiagnosticRepository(connection=db).create(diagnostic)
    with db.cursor() as cur, pytest.raises(Exception):
        cur.execute(
            """INSERT INTO transformometro.diagnostic_hypotheses
               (hypothesis_id, diagnostic_id, statement, lifecycle,
                effective_validation)
               VALUES (%s, %s, 'x', 'BOGUS', 'CURRENT')""",
            (_uid(), diagnostic.diagnostic_id),
        )
        db.commit()
    db.rollback()


def test_single_validated_conclusion_enforced(db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("slot único"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    DiagnosticRepository(connection=db).create(diagnostic)

    cid1, cid2 = _uid(), _uid()
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.diagnostic_conclusions
               (conclusion_id, diagnostic_id, statement, lifecycle)
               VALUES (%s, %s, 'v1', 'VALIDATED')""",
            (cid1, diagnostic.diagnostic_id),
        )
        db.commit()
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO transformometro.diagnostic_conclusions
                   (conclusion_id, diagnostic_id, statement, lifecycle)
                   VALUES (%s, %s, 'v2', 'VALIDATED')""",
                (cid2, diagnostic.diagnostic_id),
            )
            db.commit()
    db.rollback()


def test_causal_self_link_rejected(db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("self"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo = DiagnosticRepository(connection=db)
    repo.create(diagnostic)
    hid = _uid()
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.diagnostic_hypotheses
               (hypothesis_id, diagnostic_id, statement, lifecycle,
                effective_validation)
               VALUES (%s, %s, 'h', 'DRAFT', 'CURRENT')""",
            (hid, diagnostic.diagnostic_id),
        )
        db.commit()
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO transformometro.diagnostic_causal_links
                   (link_id, diagnostic_id, source_hypothesis_id, target_id,
                    relation)
                   VALUES (%s, %s, %s, %s, 'CONTRIBUTES_TO')""",
                (_uid(), diagnostic.diagnostic_id, hid, hid),
            )
            db.commit()
    db.rollback()


def test_problem_statement_blank_rejected(db, fixture_ids):
    with db.cursor() as cur, pytest.raises(Exception):
        cur.execute(
            """INSERT INTO transformometro.diagnostics
               (diagnostic_id, revision_id, problem_statement, version)
               VALUES (%s, %s, '   ', 1)""",
            (_uid(), fixture_ids["revisao_id"]),
        )
        db.commit()
    db.rollback()


# ---------------------------------------------------------------------------
# Version behavior across saves
# ---------------------------------------------------------------------------


def test_version_increments_once_per_save(repo, db, fixture_ids):
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("versionado"),
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    loaded = repo.get(diagnostic.diagnostic_id)
    assert repo.save(loaded, expected_version=1) == 2

    reloaded = repo.get(diagnostic.diagnostic_id)
    assert reloaded.version == 2
    assert repo.save(reloaded, expected_version=2) == 3


# ---------------------------------------------------------------------------
# Prompt 2/10 correction — freshness propagation round-trip + save fidelity
# ---------------------------------------------------------------------------


def _validated_root_aggregate(revisao_id: str) -> tuple[Diagnostic, str, str]:
    """H1 VALIDATED+CURRENT + C1 VALIDATED+CURRENT with root_cause=H1.

    Built through the real transition path so validation snapshots exist.
    """
    h1_id, c1_id = _uid(), _uid()
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=revisao_id,
        problem_statement=ProblemStatement("propagação"),
        hypotheses=[Hypothesis(hypothesis_id=h1_id, statement="causa raiz")],
    )
    diagnostic.validate_hypothesis(h1_id)
    diagnostic.add_conclusion(
        DiagnosticConclusion(
            conclusion_id=c1_id,
            statement="conclusão efetiva",
            hypothesis_ids=(h1_id,),
            root_cause=RootCauseDesignation(h1_id),
        )
    )
    diagnostic.validate_conclusion(c1_id)
    return diagnostic, h1_id, c1_id


def test_stale_root_cause_postcondition(repo, db, fixture_ids):
    """Spec §30: stale propagation persists and rehydrates identically."""
    diagnostic, h1_id, c1_id = _validated_root_aggregate(
        fixture_ids["revisao_id"]
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    loaded = repo.get(diagnostic.diagnostic_id)
    loaded.mark_hypothesis_stale_evidence(h1_id)
    assert repo.save(loaded, expected_version=1) == 2

    authoritative = repo.get(diagnostic.diagnostic_id)
    h1 = _find(authoritative.hypotheses, "hypothesis_id", h1_id)
    c1 = _find(authoritative.diagnostic_conclusions, "conclusion_id", c1_id)
    assert h1.lifecycle is ClaimLifecycle.VALIDATED
    assert h1.effective_validation is EffectiveValidation.STALE_EVIDENCE
    assert c1.lifecycle is ClaimLifecycle.VALIDATED
    assert c1.effective_validation is EffectiveValidation.STALE_EVIDENCE
    assert c1.root_cause is not None
    assert c1.root_cause.hypothesis_id == h1_id
    # the original validation snapshot stays historical (CURRENT at
    # transition time is not rewritten)
    assert c1.validation_history[0].effective_validation is (
        EffectiveValidation.CURRENT
    )


def test_revalidation_required_round_trip(repo, db, fixture_ids):
    diagnostic, h1_id, c1_id = _validated_root_aggregate(
        fixture_ids["revisao_id"]
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    loaded = repo.get(diagnostic.diagnostic_id)
    loaded.mark_hypothesis_revalidation_required(h1_id)
    assert repo.save(loaded, expected_version=1) == 2

    authoritative = repo.get(diagnostic.diagnostic_id)
    c1 = _find(authoritative.diagnostic_conclusions, "conclusion_id", c1_id)
    assert c1.effective_validation is (
        EffectiveValidation.REVALIDATION_REQUIRED
    )


def test_superseded_root_cause_round_trip(repo, db, fixture_ids):
    diagnostic, h1_id, c1_id = _validated_root_aggregate(
        fixture_ids["revisao_id"]
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    loaded = repo.get(diagnostic.diagnostic_id)
    loaded.supersede_hypothesis(h1_id)
    assert repo.save(loaded, expected_version=1) == 2

    authoritative = repo.get(diagnostic.diagnostic_id)
    h1 = _find(authoritative.hypotheses, "hypothesis_id", h1_id)
    c1 = _find(authoritative.diagnostic_conclusions, "conclusion_id", c1_id)
    assert h1.lifecycle is ClaimLifecycle.SUPERSEDED
    assert c1.lifecycle is ClaimLifecycle.VALIDATED
    assert c1.effective_validation is (
        EffectiveValidation.REVALIDATION_REQUIRED
    )


# ---------------------------------------------------------------------------
# Composite ownership constraints
# ---------------------------------------------------------------------------


def test_causal_source_cross_diagnostic_rejected(db, fixture_ids):
    repo = DiagnosticRepository(connection=db)
    a = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("A"),
    )
    b = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("B"),
        hypotheses=[Hypothesis(hypothesis_id=_uid(), statement="h de B")],
    )
    fixture_ids["created_diagnostics"] += [a.diagnostic_id, b.diagnostic_id]
    repo.create(a)
    repo.create(b)
    b_hypothesis = b.hypotheses[0].hypothesis_id
    b_finding = _uid()
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.diagnostic_findings
               (finding_id, diagnostic_id, statement, epistemic_state)
               VALUES (%s, %s, 'f de A', 'OBSERVED')""",
            (b_finding, a.diagnostic_id),
        )
        db.commit()
        with pytest.raises(Exception):
            cur.execute(
                """INSERT INTO transformometro.diagnostic_causal_links
                   (link_id, diagnostic_id, source_hypothesis_id, target_id,
                    relation)
                   VALUES (%s, %s, %s, %s, 'CONTRIBUTES_TO')""",
                (_uid(), a.diagnostic_id, b_hypothesis, b_finding),
            )
            db.commit()
    db.rollback()


def test_root_cause_cross_diagnostic_rejected(db, fixture_ids):
    repo = DiagnosticRepository(connection=db)
    a = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("A"),
    )
    b = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("B"),
        hypotheses=[Hypothesis(hypothesis_id=_uid(), statement="h de B")],
    )
    fixture_ids["created_diagnostics"] += [a.diagnostic_id, b.diagnostic_id]
    repo.create(a)
    repo.create(b)
    b_hypothesis = b.hypotheses[0].hypothesis_id
    with db.cursor() as cur, pytest.raises(Exception):
        cur.execute(
            """INSERT INTO transformometro.diagnostic_conclusions
               (conclusion_id, diagnostic_id, statement, lifecycle,
                root_cause_hypothesis_id)
               VALUES (%s, %s, 'c de A', 'DRAFT', %s)""",
            (_uid(), a.diagnostic_id, b_hypothesis),
        )
        db.commit()
    db.rollback()


# ---------------------------------------------------------------------------
# Save fidelity — fail closed, never hard-delete
# ---------------------------------------------------------------------------


def test_historical_child_omission_rejected(repo, db, fixture_ids):
    f1 = Finding(finding_id=_uid(), statement="F1")
    f2 = Finding(finding_id=_uid(), statement="F2")
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("base"),
        findings=[f1, f2],
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    # Manually constructed aggregate silently drops F2.
    partial = Diagnostic(
        diagnostic_id=diagnostic.diagnostic_id,
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("base"),
        findings=[f1],
    )
    with pytest.raises(DiagnosticFidelityError) as excinfo:
        repo.save(partial, expected_version=1)
    assert excinfo.value.code == "diagnostic.save_fidelity_mismatch"
    db.rollback()

    authoritative = repo.get(diagnostic.diagnostic_id)
    assert authoritative.version == 1
    assert {f.finding_id for f in authoritative.findings} == {
        f1.finding_id,
        f2.finding_id,
    }


def test_immutable_child_mismatch_rejected(repo, db, fixture_ids):
    f1 = Finding(finding_id=_uid(), statement="texto original")
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("base"),
        findings=[f1],
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    tampered = Diagnostic(
        diagnostic_id=diagnostic.diagnostic_id,
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("base"),
        findings=[
            Finding(finding_id=f1.finding_id, statement="texto adulterado")
        ],
    )
    with pytest.raises(DiagnosticFidelityError):
        repo.save(tampered, expected_version=1)
    db.rollback()

    authoritative = repo.get(diagnostic.diagnostic_id)
    assert authoritative.findings[0].statement == "texto original"


def test_mutation_supported_by_domain_round_trips(repo, db, fixture_ids):
    """Contrast: mutations the domain DOES authorize must persist."""
    h = Hypothesis(hypothesis_id=_uid(), statement="h")
    diagnostic = Diagnostic(
        diagnostic_id=_uid(),
        revision_id=fixture_ids["revisao_id"],
        problem_statement=ProblemStatement("mutável"),
        hypotheses=[h],
    )
    fixture_ids["created_diagnostics"].append(diagnostic.diagnostic_id)
    repo.create(diagnostic)

    loaded = repo.get(diagnostic.diagnostic_id)
    loaded.validate_hypothesis(h.hypothesis_id, note="ok")
    assert repo.save(loaded, expected_version=1) == 2

    authoritative = repo.get(diagnostic.diagnostic_id)
    h_loaded = authoritative.hypotheses[0]
    assert h_loaded.lifecycle is ClaimLifecycle.VALIDATED
    assert len(h_loaded.validation_history) == 1
