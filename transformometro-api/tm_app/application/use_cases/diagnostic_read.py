"""Diagnostic V1 — Application Read slice.

Read orchestration only: the use cases compose authorities (Diagnostic
aggregate persistence, Revision context, Revision-scoped Evidence) into
immutable read models. They never mutate state — no save/create, no
lifecycle or effective_validation changes, no audit writes.

Semantic errors carry stable codes (transport-agnostic):
``diagnostic.not_found``, ``diagnostic.revision_not_found``,
``diagnostic.read_integrity_error``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tm_app.application.ports.evidence_reader_port import (
    EvidenceReaderPort,
    EvidenceRef,
)
from tm_app.application.ports.revision_reader_port import (
    RevisionContext,
    RevisionReaderPort,
)
from tm_app.domain.diagnostic.diagnostic import (
    ClaimLifecycle,
    Diagnostic,
    EffectiveValidation,
)
from tm_app.domain.ports.diagnostic_repository_port import (
    DiagnosticRepositoryPort,
)


class DiagnosticReadError(LookupError):
    """Transport-agnostic read failure with a stable semantic code."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _raise(code: str, message: str) -> None:
    raise DiagnosticReadError(code, message)


# ---------------------------------------------------------------------------
# Read models — immutable application DTOs (never rows / HTTP schemas)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ReadSignal:
    """Calculated read-time integrity/attention signal.

    Signals are CALCULATED observations derived at read time; they never
    overwrite persisted lifecycle or effective_validation.
    """

    code: str
    detail: str


@dataclass(frozen=True)
class EvidenceLinkView:
    """One persisted EvidenceLink plus its read-time resolution.

    CONTRADICTS links are first-class — never filtered.
    """

    link_id: str
    evidence_id: str
    relation: str
    target_id: str | None
    # Derived only from entities present in the aggregate; None when the
    # link has no target or the id matches no internal entity.
    target_kind: str | None
    resolved_in_revision: bool
    evidence: EvidenceRef | None


@dataclass(frozen=True)
class DiagnosticDataQuality:
    """Explicit integrity view over the read context."""

    signals: tuple[ReadSignal, ...]
    unresolved_evidence_links: tuple[str, ...]


@dataclass(frozen=True)
class DiagnosticReadContext:
    """Aggregate + revision context + resolved evidence + quality."""

    diagnostic: Diagnostic
    revision: RevisionContext
    evidence_links: tuple[EvidenceLinkView, ...]
    data_quality: DiagnosticDataQuality


@dataclass(frozen=True)
class DiagnosticSummary:
    """Small list item — no evidence inventory, no full entity payload."""

    diagnostic_id: str
    version: int
    problem_statement: str
    findings_count: int
    hypotheses_count: int
    causal_links_count: int
    evidence_links_count: int
    conclusions_count: int
    has_validated_conclusion: bool
    revalidation_attention_required: bool


@dataclass(frozen=True)
class DiagnosticListResult:
    revision: RevisionContext
    items: tuple[DiagnosticSummary, ...]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _target_kind(diagnostic: Diagnostic, target_id: str) -> str | None:
    """Classify a link target using only entities present in the aggregate."""
    kinds: list[str] = []
    if any(f.finding_id == target_id for f in diagnostic.findings):
        kinds.append("finding")
    if any(h.hypothesis_id == target_id for h in diagnostic.hypotheses):
        kinds.append("hypothesis")
    if any(
        c.conclusion_id == target_id
        for c in diagnostic.diagnostic_conclusions
    ):
        kinds.append("conclusion")
    if len(kinds) == 1:
        return kinds[0]
    if not kinds:
        return None
    return None  # ambiguous — reported via integrity signal


def _target_is_ambiguous(diagnostic: Diagnostic, target_id: str) -> bool:
    matches = sum(
        1
        for pred in (
            lambda: any(
                f.finding_id == target_id for f in diagnostic.findings
            ),
            lambda: any(
                h.hypothesis_id == target_id for h in diagnostic.hypotheses
            ),
            lambda: any(
                c.conclusion_id == target_id
                for c in diagnostic.diagnostic_conclusions
            ),
        )
        if pred()
    )
    return matches > 1


def _attention_required(diagnostic: Diagnostic) -> bool:
    """Any VALIDATED claim whose current effective validation degraded."""
    for hypothesis in diagnostic.hypotheses:
        if (
            hypothesis.lifecycle is ClaimLifecycle.VALIDATED
            and hypothesis.effective_validation
            is not EffectiveValidation.CURRENT
        ):
            return True
    for conclusion in diagnostic.diagnostic_conclusions:
        if (
            conclusion.lifecycle is ClaimLifecycle.VALIDATED
            and conclusion.effective_validation
            is not EffectiveValidation.CURRENT
        ):
            return True
    return False


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


class GetDiagnostic:
    """Resolve one Diagnostic with revision context and evidence views."""

    def __init__(
        self,
        diagnostics: DiagnosticRepositoryPort,
        revisions: RevisionReaderPort,
        evidences: EvidenceReaderPort,
    ) -> None:
        self._diagnostics = diagnostics
        self._revisions = revisions
        self._evidences = evidences

    def execute(self, diagnostic_id: str) -> DiagnosticReadContext:
        diagnostic = self._diagnostics.get(diagnostic_id)
        if diagnostic is None:
            _raise(
                "diagnostic.not_found",
                f"diagnostic {diagnostic_id} não encontrado.",
            )

        revision = self._revisions.get(diagnostic.revision_id)
        if revision is None:
            _raise(
                "diagnostic.revision_not_found",
                f"revision {diagnostic.revision_id} do diagnostic "
                f"{diagnostic_id} não resolveu.",
            )

        # One revision-scoped inventory — never per-link lookups.
        evidence_by_id = {
            e.evidence_id: e
            for e in self._evidences.list_by_revision(diagnostic.revision_id)
        }

        signals: list[ReadSignal] = []
        views: list[EvidenceLinkView] = []
        unresolved: list[str] = []
        for link in diagnostic.evidence_links:
            evidence = evidence_by_id.get(link.evidence_id)
            resolved = evidence is not None
            if not resolved:
                unresolved.append(link.link_id)
                signals.append(
                    ReadSignal(
                        code="evidence_link_unresolved_in_revision",
                        detail=(
                            f"EvidenceLink {link.link_id} → evidence "
                            f"{link.evidence_id} não resolve na revision "
                            f"{diagnostic.revision_id}."
                        ),
                    )
                )
            target_kind: str | None = None
            if link.target_id is not None:
                if _target_is_ambiguous(diagnostic, link.target_id):
                    signals.append(
                        ReadSignal(
                            code="evidence_link_target_ambiguous",
                            detail=(
                                f"EvidenceLink {link.link_id} target "
                                f"{link.target_id} corresponde a mais de "
                                f"um tipo de entidade."
                            ),
                        )
                    )
                else:
                    target_kind = _target_kind(diagnostic, link.target_id)
            views.append(
                EvidenceLinkView(
                    link_id=link.link_id,
                    evidence_id=link.evidence_id,
                    relation=link.relation.value,
                    target_id=link.target_id,
                    target_kind=target_kind,
                    resolved_in_revision=resolved,
                    evidence=evidence,
                )
            )

        if _attention_required(diagnostic):
            signals.append(
                ReadSignal(
                    code="revalidation_attention_required",
                    detail=(
                        "Existe claim VALIDATED com effective_validation "
                        "diferente de CURRENT."
                    ),
                )
            )

        return DiagnosticReadContext(
            diagnostic=diagnostic,
            revision=revision,
            evidence_links=tuple(views),
            data_quality=DiagnosticDataQuality(
                signals=tuple(signals),
                unresolved_evidence_links=tuple(unresolved),
            ),
        )


class ListDiagnosticsByRevision:
    """Revision-scoped summaries — no evidence fan-out per diagnostic."""

    def __init__(
        self,
        diagnostics: DiagnosticRepositoryPort,
        revisions: RevisionReaderPort,
    ) -> None:
        self._diagnostics = diagnostics
        self._revisions = revisions

    def execute(self, revision_id: str) -> DiagnosticListResult:
        revision = self._revisions.get(revision_id)
        if revision is None:
            _raise(
                "diagnostic.revision_not_found",
                f"revision {revision_id} não encontrada.",
            )

        diagnostics = self._diagnostics.list_by_revision(revision_id)
        items = tuple(
            DiagnosticSummary(
                diagnostic_id=d.diagnostic_id,
                version=d.version,
                problem_statement=d.problem_statement.text,
                findings_count=len(d.findings),
                hypotheses_count=len(d.hypotheses),
                causal_links_count=len(d.causal_links),
                evidence_links_count=len(d.evidence_links),
                conclusions_count=len(d.diagnostic_conclusions),
                has_validated_conclusion=any(
                    c.lifecycle is ClaimLifecycle.VALIDATED
                    for c in d.diagnostic_conclusions
                ),
                revalidation_attention_required=_attention_required(d),
            )
            for d in diagnostics
        )
        return DiagnosticListResult(revision=revision, items=items)


# Re-export for callers that only need the port types (keeps the read
# surface importable from a single application module).
__all__ = [
    "DiagnosticDataQuality",
    "DiagnosticListResult",
    "DiagnosticReadContext",
    "DiagnosticReadError",
    "DiagnosticSummary",
    "EvidenceLinkView",
    "GetDiagnostic",
    "ListDiagnosticsByRevision",
    "ReadSignal",
]
