"""Diagnostic V1 — Application Read tests.

Unit layer covers use-case orchestration with in-memory fakes; adapter
layer runs the thin readers against a real PostgreSQL (``TM_TEST_DSN``)
to prove canonical authority behavior, revision scoping and the
side-effect-free contract end to end.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from tm_app.application.ports.evidence_reader_port import EvidenceRef
from tm_app.application.ports.revision_reader_port import RevisionContext
from tm_app.application.use_cases.diagnostic_read import (
    DiagnosticReadError,
    GetDiagnostic,
    ListDiagnosticsByRevision,
)
from tm_app.domain.diagnostic.diagnostic import (
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
from tm_app.infrastructure.persistence.repositories.diagnostic_repository import (  # noqa: E402
    DiagnosticRepository,
)

REV_A, REV_B = str(uuid4()), str(uuid4())
EV1, EV2, EV3 = str(uuid4()), str(uuid4()), str(uuid4())


# ---------------------------------------------------------------------------
# In-memory fakes (ports only — never persistence internals)
# ---------------------------------------------------------------------------


class FakeDiagnosticRepo:
    def __init__(self) -> None:
        self._store: dict[str, Diagnostic] = {}
        self.save = MagicMock()
        self.create = MagicMock()

    def seed(self, diagnostic: Diagnostic) -> None:
        self._store[diagnostic.diagnostic_id] = diagnostic

    def get(self, diagnostic_id):
        return self._store.get(diagnostic_id)

    def list_by_revision(self, revision_id):
        return [
            d
            for d in self._store.values()
            if d.revision_id == revision_id
        ]


class FakeRevisionReader:
    def __init__(self) -> None:
        self._store: dict[str, RevisionContext] = {
            REV_A: RevisionContext(
                revision_id=REV_A,
                processo_id=str(uuid4()),
                instancia_id=str(uuid4()),
                versao_revisao="v2.0.0",
                cenario_tipo="as_is",
                revisao_referencia_id=str(uuid4()),
            ),
            REV_B: RevisionContext(
                revision_id=REV_B,
                processo_id=str(uuid4()),
                instancia_id=str(uuid4()),
                versao_revisao="v1.0.0",
                cenario_tipo="baseline",
                revisao_referencia_id=None,
            ),
        }

    def get(self, revision_id):
        return self._store.get(revision_id)


class FakeEvidenceReader:
    def __init__(self) -> None:
        self._store: dict[str, list[EvidenceRef]] = {
            REV_A: [
                EvidenceRef(EV1, REV_A, "anexo", "e1.pdf", None),
                EvidenceRef(EV2, REV_A, "documento", "e2.md", "nota"),
                EvidenceRef(EV3, REV_A, "foto", "e3.jpg", None),
            ],
            REV_B: [],
        }
        self.calls: list[str] = []

    def list_by_revision(self, revision_id):
        self.calls.append(revision_id)
        return list(self._store.get(revision_id, []))


def _diagnostic(revisao_id: str = REV_A, **kwargs) -> Diagnostic:
    kwargs.setdefault(
        "problem_statement", ProblemStatement("problema base")
    )
    return Diagnostic(
        diagnostic_id=str(uuid4()), revision_id=revisao_id, **kwargs
    )


def _full_diagnostic(revisao_id: str = REV_A) -> Diagnostic:
    d = _diagnostic(
        revisao_id,
        findings=[
            Finding(
                finding_id=str(uuid4()),
                statement="f1",
                epistemic_state=EpistemicState.OBSERVED,
            )
        ],
        hypotheses=[
            Hypothesis(
                hypothesis_id=str(uuid4()),
                statement="h1",
                lifecycle=ClaimLifecycle.VALIDATED,
                effective_validation=EffectiveValidation.CURRENT,
            )
        ],
    )
    h1 = d.hypotheses[0].hypothesis_id
    d.add_evidence_link(
        EvidenceLink(
            link_id=str(uuid4()),
            evidence_id=EV1,
            relation=EvidenceRelation.SUPPORTS,
            target_id=h1,
        )
    )
    d.add_evidence_link(
        EvidenceLink(
            link_id=str(uuid4()),
            evidence_id=EV2,
            relation=EvidenceRelation.CONTRADICTS,
            target_id=d.findings[0].finding_id,
        )
    )
    d.add_evidence_link(
        EvidenceLink(
            link_id=str(uuid4()),
            evidence_id=EV3,
            relation=EvidenceRelation.CONTEXTUALIZES,
        )
    )
    return d


def _use_cases():
    diagnostics = FakeDiagnosticRepo()
    revisions = FakeRevisionReader()
    evidences = FakeEvidenceReader()
    get = GetDiagnostic(diagnostics, revisions, evidences)
    listing = ListDiagnosticsByRevision(diagnostics, revisions)
    return diagnostics, revisions, evidences, get, listing


# ---------------------------------------------------------------------------
# GET — A..J
# ---------------------------------------------------------------------------


def test_get_returns_aggregate_revision_and_evidence_views():
    diagnostics, _, evidences, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)

    ctx = get.execute(d.diagnostic_id)
    assert ctx.diagnostic.diagnostic_id == d.diagnostic_id
    assert ctx.diagnostic.revision_id == REV_A
    assert ctx.revision.revision_id == REV_A
    assert ctx.revision.versao_revisao == "v2.0.0"
    assert evidences.calls == [REV_A]  # single revision-scoped inventory
    assert len(ctx.evidence_links) == 3
    assert all(v.resolved_in_revision for v in ctx.evidence_links)
    assert ctx.data_quality.signals == ()


def test_get_missing_diagnostic_raises_not_found():
    _, _, _, get, _ = _use_cases()
    with pytest.raises(DiagnosticReadError) as excinfo:
        get.execute(str(uuid4()))
    assert excinfo.value.code == "diagnostic.not_found"


def test_get_revision_unresolved_raises():
    diagnostics, _, _, get, _ = _use_cases()
    d = _diagnostic(revisao_id=str(uuid4()))  # unknown revision
    diagnostics.seed(d)
    with pytest.raises(DiagnosticReadError) as excinfo:
        get.execute(d.diagnostic_id)
    assert excinfo.value.code == "diagnostic.revision_not_found"


def test_supports_link_resolves_with_evidence():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)
    view = next(v for v in ctx.evidence_links if v.relation == "SUPPORTS")
    assert view.resolved_in_revision
    assert view.evidence is not None
    assert view.evidence.evidence_id == EV1
    assert view.target_kind == "hypothesis"


def test_contradicts_link_visible_and_resolved():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)
    view = next(v for v in ctx.evidence_links if v.relation == "CONTRADICTS")
    assert view.resolved_in_revision
    assert view.evidence is not None
    assert view.evidence.evidence_id == EV2
    assert view.target_kind == "finding"


def test_contextualizes_link_resolves_without_target():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)
    view = next(
        v for v in ctx.evidence_links if v.relation == "CONTEXTUALIZES"
    )
    assert view.resolved_in_revision
    assert view.target_id is None
    assert view.target_kind is None


def test_unresolved_evidence_warns_without_fallback_or_mutation():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    foreign_evidence = str(uuid4())  # never present in REV_A inventory
    d.add_evidence_link(
        EvidenceLink(
            link_id=str(uuid4()),
            evidence_id=foreign_evidence,
            relation=EvidenceRelation.SUPPORTS,
        )
    )
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)

    view = next(
        v for v in ctx.evidence_links if v.evidence_id == foreign_evidence
    )
    assert not view.resolved_in_revision
    assert view.evidence is None
    assert view.link_id in ctx.data_quality.unresolved_evidence_links
    assert any(
        s.code == "evidence_link_unresolved_in_revision"
        for s in ctx.data_quality.signals
    )
    # link remains visible — never removed, never substituted
    assert len(ctx.evidence_links) == 4
    # aggregate untouched
    assert len(ctx.diagnostic.evidence_links) == 4


def test_validated_stale_conclusion_state_preserved():
    diagnostics, _, _, get, _ = _use_cases()
    h = Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
    )
    c = DiagnosticConclusion(
        conclusion_id=str(uuid4()),
        statement="c",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    d = _diagnostic(hypotheses=[h], diagnostic_conclusions=[c])
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)

    loaded = ctx.diagnostic.diagnostic_conclusions[0]
    assert loaded.lifecycle is ClaimLifecycle.VALIDATED
    assert loaded.effective_validation is EffectiveValidation.STALE_EVIDENCE
    assert any(
        s.code == "revalidation_attention_required"
        for s in ctx.data_quality.signals
    )


def test_root_cause_states_preserved():
    diagnostics, _, _, get, _ = _use_cases()
    h = Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
    )
    c = DiagnosticConclusion(
        conclusion_id=str(uuid4()),
        statement="c",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    d = _diagnostic(hypotheses=[h], diagnostic_conclusions=[c])
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)

    conclusion = ctx.diagnostic.diagnostic_conclusions[0]
    hypothesis = ctx.diagnostic.hypotheses[0]
    assert conclusion.root_cause is not None
    assert conclusion.root_cause.hypothesis_id == h.hypothesis_id
    # historically VALIDATED + currently stale — both preserved verbatim
    assert hypothesis.lifecycle is ClaimLifecycle.VALIDATED
    assert hypothesis.effective_validation is (
        EffectiveValidation.STALE_EVIDENCE
    )
    assert conclusion.lifecycle is ClaimLifecycle.VALIDATED


def test_version_unchanged_after_read():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    before = d.version
    ctx = get.execute(d.diagnostic_id)
    assert ctx.diagnostic.version == before


# ---------------------------------------------------------------------------
# LIST
# ---------------------------------------------------------------------------


def test_list_empty_revision():
    _, _, _, _, listing = _use_cases()
    result = listing.execute(REV_A)
    assert result.items == ()
    assert result.revision.revision_id == REV_A


def test_list_one_diagnostic_summary_fields():
    diagnostics, _, _, _, listing = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    result = listing.execute(REV_A)
    assert len(result.items) == 1
    s = result.items[0]
    assert s.diagnostic_id == d.diagnostic_id
    assert s.version == d.version
    assert s.problem_statement == "problema base"
    assert s.findings_count == 1
    assert s.hypotheses_count == 1
    assert s.evidence_links_count == 3
    assert s.conclusions_count == 0
    assert s.has_validated_conclusion is False
    assert s.revalidation_attention_required is False


def test_list_multiple_deterministic_order():
    """Ordering is an Application contract — independent of repo order."""
    diagnostics, _, _, _, listing = _use_cases()
    # Fake repo returns D3, D1, D2 (arbitrary persistence order).
    for did in ("d-003", "d-001", "d-002"):
        diagnostics.seed(
            Diagnostic(
                diagnostic_id=did,
                revision_id=REV_A,
                problem_statement=ProblemStatement(f"p {did}"),
            )
        )
    first = listing.execute(REV_A)
    second = listing.execute(REV_A)
    assert [i.diagnostic_id for i in first.items] == [
        "d-001",
        "d-002",
        "d-003",
    ]
    assert [i.diagnostic_id for i in second.items] == [
        i.diagnostic_id for i in first.items
    ]


def test_list_scoped_to_requested_revision():
    diagnostics, _, _, _, listing = _use_cases()
    diagnostics.seed(_diagnostic(revisao_id=REV_A))
    diagnostics.seed(_diagnostic(revisao_id=REV_B))
    result = listing.execute(REV_A)
    assert len(result.items) == 1
    assert all(i.diagnostic_id != "" for i in result.items)


def test_list_missing_revision_raises():
    _, _, _, _, listing = _use_cases()
    with pytest.raises(DiagnosticReadError) as excinfo:
        listing.execute(str(uuid4()))
    assert excinfo.value.code == "diagnostic.revision_not_found"


# ---------------------------------------------------------------------------
# Side-effect-free contract
# ---------------------------------------------------------------------------


def test_get_and_list_never_write():
    diagnostics, _, _, get, listing = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    get.execute(d.diagnostic_id)
    listing.execute(REV_A)
    diagnostics.save.assert_not_called()
    diagnostics.create.assert_not_called()


def test_read_does_not_mutate_aggregate_state():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    h = d.hypotheses[0]
    before = (h.lifecycle, h.effective_validation, d.version)
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)
    h_after = ctx.diagnostic.hypotheses[0]
    assert (h_after.lifecycle, h_after.effective_validation) == before[:2]
    assert ctx.diagnostic.version == before[2]


# ---------------------------------------------------------------------------
# Deep read-only contract (Prompt 3 correction)
# ---------------------------------------------------------------------------


# A — read surface exposes no aggregate mutation methods
def test_read_view_has_no_mutation_methods():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    view = get.execute(d.diagnostic_id).diagnostic
    for method in (
        "add_finding",
        "add_hypothesis",
        "add_causal_link",
        "add_evidence_link",
        "add_conclusion",
        "validate_hypothesis",
        "validate_conclusion",
        "reject_hypothesis",
        "reject_conclusion",
        "supersede_hypothesis",
        "supersede_conclusion",
        "mark_hypothesis_stale_evidence",
        "mark_hypothesis_revalidation_required",
    ):
        assert not hasattr(view, method), method


# B — view collections are read-only tuples
def test_read_view_collections_are_tuples():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    view = get.execute(d.diagnostic_id).diagnostic
    for collection in (
        view.findings,
        view.hypotheses,
        view.causal_links,
        view.evidence_links,
        view.diagnostic_conclusions,
    ):
        assert isinstance(collection, tuple)
        with pytest.raises(AttributeError):
            collection.append(object())


# C — view fields cannot be reassigned
def test_read_view_fields_frozen():
    diagnostics, _, _, get, _ = _use_cases()
    d = _full_diagnostic()
    diagnostics.seed(d)
    view = get.execute(d.diagnostic_id).diagnostic
    with pytest.raises(Exception):
        view.version = 99
    with pytest.raises(Exception):
        view.problem_statement = ProblemStatement("outro")


# D — mutating the source aggregate does not alter the returned snapshot
def test_source_mutation_does_not_alias_snapshot():
    diagnostics, _, _, get, _ = _use_cases()
    d = _diagnostic(
        hypotheses=[
            Hypothesis(hypothesis_id=str(uuid4()), statement="h1")
        ]
    )
    diagnostics.seed(d)
    ctx = get.execute(d.diagnostic_id)
    snapshot_h = ctx.diagnostic.hypotheses[0]
    assert snapshot_h.lifecycle is ClaimLifecycle.DRAFT
    assert len(ctx.diagnostic.findings) == 0

    # consumer mutates the aggregate AFTER the read returned
    d.validate_hypothesis(d.hypotheses[0].hypothesis_id)
    d.add_finding(Finding(finding_id=str(uuid4()), statement="novo"))

    # snapshot stays at read-time state
    assert ctx.diagnostic.hypotheses[0].lifecycle is ClaimLifecycle.DRAFT
    assert len(ctx.diagnostic.findings) == 0
    # and it is a different object than the mutated entity
    assert ctx.diagnostic.hypotheses[0] is not d.hypotheses[0]


# E — persisted semantics preserved verbatim in the view
def test_view_preserves_epistemic_lifecycle_effective():
    diagnostics, _, _, get, _ = _use_cases()
    h = Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
    )
    d = _diagnostic(hypotheses=[h])
    diagnostics.seed(d)
    view = get.execute(d.diagnostic_id).diagnostic
    h_view = view.hypotheses[0]
    assert h_view.epistemic_state is EpistemicState.INFERRED
    assert h_view.lifecycle is ClaimLifecycle.VALIDATED
    assert h_view.effective_validation is (
        EffectiveValidation.STALE_EVIDENCE
    )


# ---------------------------------------------------------------------------
# Real-DB adapter tests (skip without TM_TEST_DSN)
# ---------------------------------------------------------------------------


psycopg = pytest.importorskip("psycopg")
from psycopg.rows import dict_row  # noqa: E402

from tm_app.infrastructure.persistence.repositories.diagnostic_readers import (  # noqa: E402
    EvidenceReaderAdapter,
    RevisionReaderAdapter,
)
from tm_app.infrastructure.persistence.repositories.revision_evidence_repository import (  # noqa: E402
    RevisaoEvidenceRepository,
)
from tm_app.infrastructure.persistence.repositories.revision_repository import (  # noqa: E402
    RevisaoRepository,
)

_DSN = os.getenv("TM_TEST_DSN", "").strip()


def _connect():
    return psycopg.connect(_DSN, row_factory=dict_row, autocommit=False)


@pytest.fixture(scope="module")
def db():
    if not _DSN:
        pytest.skip("TM_TEST_DSN ausente — adapter tests requerem PG real.")
    try:
        conn = _connect()
    except Exception as exc:  # pragma: no cover
        pytest.skip(f"Postgres de teste indisponível: {exc}")
    yield conn
    conn.close()


@pytest.fixture()
def anchors(db):
    processo_id = str(uuid4())
    filial_id = str(uuid4())
    instancia_id = str(uuid4())
    revisao_a = str(uuid4())
    revisao_b = str(uuid4())
    evidencias = [str(uuid4()) for _ in range(2)]
    deleted_evidence = str(uuid4())
    created: list[str] = []
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.filiais
               (filial_id, codigo_filial, nome_filial)
               VALUES (%s, %s, %s)""",
            (filial_id, f"F{filial_id[:6]}", "filial teste"),
        )
        cur.execute(
            """INSERT INTO transformometro.processos
               (processo_id, codigo_processo, nome_processo)
               VALUES (%s, %s, %s)""",
            (processo_id, f"RD-{processo_id[:8]}", "read anchors"),
        )
        cur.execute(
            """INSERT INTO transformometro.processo_instancias
               (instancia_id, processo_id, filial_id)
               VALUES (%s, %s, %s)""",
            (instancia_id, processo_id, filial_id),
        )
        for rid, ver in ((revisao_a, "vA"), (revisao_b, "vB")):
            cur.execute(
                """INSERT INTO transformometro.revisoes
                   (revisao_id, processo_id, instancia_id, versao_revisao,
                    chave_unica_processo_revisao, cenario_tipo,
                    data_inicio_vigencia)
                   VALUES (%s, %s, %s, %s, %s, 'as_is', '2026-01-01')""",
                (
                    rid,
                    processo_id,
                    instancia_id,
                    ver,
                    f"key-{rid[:8]}",
                ),
            )
        for eid in evidencias:
            cur.execute(
                """INSERT INTO transformometro.revisao_evidencias
                   (evidencia_id, revisao_id, tipo, nome_arquivo)
                   VALUES (%s, %s, 'anexo', %s)""",
                (eid, revisao_a, f"{eid[:8]}.pdf"),
            )
        cur.execute(
            """INSERT INTO transformometro.revisao_evidencias
               (evidencia_id, revisao_id, tipo, nome_arquivo, deleted_at)
               VALUES (%s, %s, 'anexo', 'del.pdf', NOW())""",
            (deleted_evidence, revisao_a),
        )
    db.commit()
    yield {
        "processo_id": processo_id,
        "filial_id": filial_id,
        "instancia_id": instancia_id,
        "revisao_a": revisao_a,
        "revisao_b": revisao_b,
        "evidencias": evidencias,
        "deleted_evidence": deleted_evidence,
        "created_diagnostics": created,
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
        cur.execute(
            "DELETE FROM transformometro.revisao_evidencias"
            " WHERE revisao_id IN (%s, %s)",
            (revisao_a, revisao_b),
        )
        cur.execute(
            "DELETE FROM transformometro.revisoes"
            " WHERE revisao_id IN (%s, %s)",
            (revisao_a, revisao_b),
        )
        cur.execute(
            "DELETE FROM transformometro.processo_instancias"
            " WHERE instancia_id = %s",
            (instancia_id,),
        )
        cur.execute(
            "DELETE FROM transformometro.processos WHERE processo_id = %s",
            (processo_id,),
        )
        cur.execute(
            "DELETE FROM transformometro.filiais WHERE filial_id = %s",
            (filial_id,),
        )
    db.commit()


def test_revision_reader_returns_canonical_fields(db, anchors):
    reader = RevisionReaderAdapter(RevisaoRepository(connection=db))
    ctx = reader.get(anchors["revisao_a"])
    assert ctx is not None
    assert ctx.revision_id == anchors["revisao_a"]
    assert ctx.processo_id == anchors["processo_id"]
    assert ctx.instancia_id is not None
    assert ctx.versao_revisao == "vA"
    assert ctx.cenario_tipo == "as_is"
    # only canonical fields — no row payload leaks
    assert not hasattr(ctx, "deletado")


def test_revision_reader_missing_returns_none(db, anchors):
    reader = RevisionReaderAdapter(RevisaoRepository(connection=db))
    assert reader.get(str(uuid4())) is None


def test_evidence_reader_scoped_and_excludes_soft_deleted(db, anchors):
    reader = EvidenceReaderAdapter(
        RevisaoEvidenceRepository(connection=db)
    )
    evidences = reader.list_by_revision(anchors["revisao_a"])
    ids = {e.evidence_id for e in evidences}
    assert ids == set(anchors["evidencias"])
    assert anchors["deleted_evidence"] not in ids
    assert all(e.revisao_id == anchors["revisao_a"] for e in evidences)
    assert reader.list_by_revision(anchors["revisao_b"]) == []


def test_get_end_to_end_real_repo_and_readers(db, anchors):
    repo = DiagnosticRepository(connection=db)
    h_id = str(uuid4())
    d = Diagnostic(
        diagnostic_id=str(uuid4()),
        revision_id=anchors["revisao_a"],
        problem_statement=ProblemStatement("e2e"),
        hypotheses=[Hypothesis(hypothesis_id=h_id, statement="h")],
        evidence_links=[
            EvidenceLink(
                link_id=str(uuid4()),
                evidence_id=anchors["evidencias"][0],
                relation=EvidenceRelation.SUPPORTS,
                target_id=h_id,
            )
        ],
    )
    anchors["created_diagnostics"].append(d.diagnostic_id)
    repo.create(d)

    get = GetDiagnostic(
        repo,
        RevisionReaderAdapter(RevisaoRepository(connection=db)),
        EvidenceReaderAdapter(RevisaoEvidenceRepository(connection=db)),
    )
    ctx = get.execute(d.diagnostic_id)
    assert ctx.revision.revision_id == anchors["revisao_a"]
    assert ctx.evidence_links[0].resolved_in_revision
    assert ctx.evidence_links[0].target_kind == "hypothesis"

    # persisted state untouched by the read
    with db.cursor() as cur:
        cur.execute(
            "SELECT version, updated_at FROM transformometro.diagnostics"
            " WHERE diagnostic_id = %s",
            (d.diagnostic_id,),
        )
        row = cur.fetchone()
    assert row["version"] == 1


def test_cross_revision_evidence_fails_closed(db, anchors):
    """Evidence of revision B linked in a revision-A diagnostic:
    unresolved locally — no cross-revision fallback."""
    repo = DiagnosticRepository(connection=db)
    foreign_evidence = str(uuid4())
    with db.cursor() as cur:
        cur.execute(
            """INSERT INTO transformometro.revisao_evidencias
               (evidencia_id, revisao_id, tipo, nome_arquivo)
               VALUES (%s, %s, 'anexo', 'other.pdf')""",
            (foreign_evidence, anchors["revisao_b"]),
        )
    db.commit()

    d = Diagnostic(
        diagnostic_id=str(uuid4()),
        revision_id=anchors["revisao_a"],
        problem_statement=ProblemStatement("cross"),
        evidence_links=[
            EvidenceLink(
                link_id=str(uuid4()),
                evidence_id=foreign_evidence,
                relation=EvidenceRelation.SUPPORTS,
            )
        ],
    )
    anchors["created_diagnostics"].append(d.diagnostic_id)
    repo.create(d)

    get = GetDiagnostic(
        repo,
        RevisionReaderAdapter(RevisaoRepository(connection=db)),
        EvidenceReaderAdapter(RevisaoEvidenceRepository(connection=db)),
    )
    ctx = get.execute(d.diagnostic_id)
    view = ctx.evidence_links[0]
    assert not view.resolved_in_revision
    assert view.evidence is None
    assert view.link_id in ctx.data_quality.unresolved_evidence_links
    # link stays visible; aggregate unmutated
    assert len(ctx.diagnostic.evidence_links) == 1
