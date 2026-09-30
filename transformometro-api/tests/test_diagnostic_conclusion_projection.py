"""Diagnostic V1 — Conclusion read-projection regression.

Guards the transport contract of ``project_conclusion`` / the shared
read pipeline (Portal HTTP + TÉO MCP consume ``project_read_context``).

EXECUTION-DRIFT regression: the projection previously read a nonexistent
``conclusion.root_cause_hypothesis_id`` attribute, so any Diagnostic
holding a Conclusion failed the canonical GET with AttributeError→500.
The canonical domain shape is ``DiagnosticConclusion.root_cause`` —
an optional ``RootCauseDesignation`` whose ``hypothesis_id`` is the only
source for the external ``root_cause_hypothesis_id`` field.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock
from uuid import uuid4

from tm_app.application.ports.evidence_reader_port import EvidenceRef
from tm_app.application.ports.revision_reader_port import RevisionContext
from tm_app.application.use_cases.diagnostic_read import (
    GetDiagnostic,
    ListDiagnosticsByRevision,
)
from tm_app.domain.diagnostic.diagnostic import (
    ClaimLifecycle,
    Diagnostic,
    DiagnosticConclusion,
    EffectiveValidation,
    EpistemicState,
    Hypothesis,
    ProblemStatement,
    Provenance,
    ProvenanceOrigin,
    RootCauseDesignation,
    ValidationSnapshot,
)
from tm_app.interface.diagnostic_projection import (
    project_conclusion,
    project_read_context,
    project_summary,
)

REV_A = str(uuid4())


def _conclusion(**kwargs) -> DiagnosticConclusion:
    kwargs.setdefault("conclusion_id", str(uuid4()))
    kwargs.setdefault("statement", "conclusão de teste")
    return DiagnosticConclusion(**kwargs)


def _concluded_diagnostic(
    conclusion: DiagnosticConclusion, **kwargs
) -> Diagnostic:
    kwargs.setdefault("diagnostic_id", str(uuid4()))
    kwargs.setdefault("revision_id", REV_A)
    kwargs.setdefault(
        "problem_statement", ProblemStatement("problema base")
    )
    kwargs.setdefault("diagnostic_conclusions", [conclusion])
    return Diagnostic(**kwargs)


# ---------------------------------------------------------------------------
# §8 — direct projection: root cause mapping
# ---------------------------------------------------------------------------


def test_project_conclusion_without_root_cause():
    projected = project_conclusion(_conclusion(root_cause=None))
    assert projected["root_cause_hypothesis_id"] is None


def test_project_conclusion_with_root_cause():
    projected = project_conclusion(
        _conclusion(root_cause=RootCauseDesignation("H1"))
    )
    assert projected["root_cause_hypothesis_id"] == "H1"


def test_project_conclusion_preserves_all_fields():
    hypothesis_id = str(uuid4())
    finding_id = str(uuid4())
    c = _conclusion(
        rationale="rationale longo",
        hypothesis_ids=(hypothesis_id,),
        finding_ids=(finding_id,),
        root_cause=RootCauseDesignation(hypothesis_id),
        provenance=Provenance(ProvenanceOrigin.USER, "op"),
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
        validation_history=(
            ValidationSnapshot(
                from_lifecycle=ClaimLifecycle.DRAFT,
                to_lifecycle=ClaimLifecycle.VALIDATED,
                effective_validation=EffectiveValidation.CURRENT,
                note="ok",
            ),
        ),
    )
    projected = project_conclusion(c)
    assert projected["conclusion_id"] == c.conclusion_id
    assert projected["statement"] == c.statement
    assert projected["rationale"] == "rationale longo"
    assert projected["hypothesis_ids"] == [hypothesis_id]
    assert projected["finding_ids"] == [finding_id]
    assert (
        projected["root_cause_hypothesis_id"] == hypothesis_id
    )
    assert projected["lifecycle"] == "VALIDATED"
    assert projected["effective_validation"] == "CURRENT"
    assert projected["epistemic_state"] == "INFERRED"
    assert projected["provenance"] == {
        "origin": "USER",
        "detail": "op",
    }
    assert projected["validation_history"] == [
        {
            "from_lifecycle": "DRAFT",
            "to_lifecycle": "VALIDATED",
            "effective_validation": "CURRENT",
            "note": "ok",
        }
    ]
    # No nested transport object leaks the designation value object.
    assert isinstance(projected["root_cause_hypothesis_id"], str)
    assert "root_cause" not in projected


# ---------------------------------------------------------------------------
# §10/§11/§12 — epistemic, lifecycle and effective-validation invariants
# ---------------------------------------------------------------------------


def test_validated_conclusion_remains_epistemically_inferred():
    projected = project_conclusion(
        _conclusion(lifecycle=ClaimLifecycle.VALIDATED)
    )
    assert projected["lifecycle"] == "VALIDATED"
    # VALIDATED != FACT — epistemic nature never upgrades.
    assert projected["epistemic_state"] == "INFERRED"


def test_lifecycle_states_project_verbatim():
    for lifecycle in ClaimLifecycle:
        projected = project_conclusion(
            _conclusion(lifecycle=lifecycle)
        )
        assert projected["lifecycle"] == lifecycle.value


def test_effective_validation_states_project_verbatim():
    for effective in EffectiveValidation:
        projected = project_conclusion(
            _conclusion(
                lifecycle=ClaimLifecycle.VALIDATED,
                effective_validation=effective,
            )
        )
        assert projected["effective_validation"] == effective.value


# ---------------------------------------------------------------------------
# §14 — full read pipeline: GetDiagnostic → project_read_context
# ---------------------------------------------------------------------------


class _FakeDiagnosticRepo:
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


class _FakeRevisionReader:
    def get(self, revision_id):
        if revision_id == REV_A:
            return RevisionContext(
                revision_id=REV_A,
                processo_id=str(uuid4()),
                instancia_id=str(uuid4()),
                versao_revisao="v1",
                cenario_tipo="as_is",
                revisao_referencia_id=None,
            )
        return None


class _FakeEvidenceReader:
    def list_by_revision(self, revision_id):
        return []


def test_full_read_pipeline_with_conclusion_no_root_cause():
    repo = _FakeDiagnosticRepo()
    d = _concluded_diagnostic(_conclusion(root_cause=None))
    repo.seed(d)

    ctx = GetDiagnostic(
        repo, _FakeRevisionReader(), _FakeEvidenceReader()
    ).execute(d.diagnostic_id)
    payload = project_read_context(ctx)

    json.dumps(payload)  # transport-safe
    assert payload["diagnostic"]["conclusions"][0][
        "root_cause_hypothesis_id"
    ] is None
    repo.save.assert_not_called()


def test_full_read_pipeline_with_designated_root_cause():
    repo = _FakeDiagnosticRepo()
    h = Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
    )
    c = _conclusion(
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.CURRENT,
        validation_history=(
            ValidationSnapshot(
                from_lifecycle=ClaimLifecycle.DRAFT,
                to_lifecycle=ClaimLifecycle.VALIDATED,
                effective_validation=EffectiveValidation.CURRENT,
                note=None,
            ),
        ),
    )
    d = _concluded_diagnostic(c, hypotheses=[h])
    repo.seed(d)

    ctx = GetDiagnostic(
        repo, _FakeRevisionReader(), _FakeEvidenceReader()
    ).execute(d.diagnostic_id)
    projected = project_read_context(ctx)["diagnostic"][
        "conclusions"
    ][0]

    assert projected["root_cause_hypothesis_id"] == h.hypothesis_id
    assert projected["lifecycle"] == "VALIDATED"
    assert projected["effective_validation"] == "CURRENT"
    assert projected["epistemic_state"] == "INFERRED"
    repo.save.assert_not_called()


def test_read_pipeline_validated_stale_and_revalidation_required():
    """VALIDATED + degraded effective_validation survives the projection."""
    repo = _FakeDiagnosticRepo()
    for effective in (
        EffectiveValidation.STALE_EVIDENCE,
        EffectiveValidation.REVALIDATION_REQUIRED,
    ):
        d = _concluded_diagnostic(
            _conclusion(
                lifecycle=ClaimLifecycle.VALIDATED,
                effective_validation=effective,
            )
        )
        repo.seed(d)
        ctx = GetDiagnostic(
            repo, _FakeRevisionReader(), _FakeEvidenceReader()
        ).execute(d.diagnostic_id)
        projected = project_read_context(ctx)["diagnostic"][
            "conclusions"
        ][0]
        assert projected["lifecycle"] == "VALIDATED"
        assert projected["effective_validation"] == effective.value
        assert projected["epistemic_state"] == "INFERRED"


# ---------------------------------------------------------------------------
# §16 — list summary regression (counts only; no conclusion payload in list)
# ---------------------------------------------------------------------------


def test_list_summary_counts_conclusions_without_payload():
    repo = _FakeDiagnosticRepo()
    h = Hypothesis(
        hypothesis_id=str(uuid4()),
        statement="h",
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
    )
    validated_stale = _conclusion(
        lifecycle=ClaimLifecycle.VALIDATED,
        effective_validation=EffectiveValidation.STALE_EVIDENCE,
        hypothesis_ids=(h.hypothesis_id,),
        root_cause=RootCauseDesignation(h.hypothesis_id),
    )
    draft = _conclusion()
    repo.seed(
        _concluded_diagnostic(
            validated_stale,
            hypotheses=[h],
            diagnostic_conclusions=[validated_stale, draft],
        )
    )
    result = ListDiagnosticsByRevision(
        repo, _FakeRevisionReader()
    ).execute(REV_A)
    item = project_summary(result.items[0])
    assert item["conclusions_count"] == 2
    assert item["has_validated_conclusion"] is True
    assert item["revalidation_attention_required"] is True
    assert "root_cause_hypothesis_id" not in item
    assert "conclusions" not in item
