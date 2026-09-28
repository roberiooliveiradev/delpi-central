"""Diagnostic V1 — Domain Kernel (pure stdlib).

Aggregate boundary::

    Revision
    └── 0..N Diagnostic  (aggregate root)

    Diagnostic
    ├── exactly 1 ProblemStatement (value object)
    ├── Finding *
    ├── Hypothesis *
    ├── CausalLink *
    ├── EvidenceLink *
    └── DiagnosticConclusion *

Revision is the contextual anchor; Evidence stays an external authority owned
by the Revision. This kernel never imports infrastructure, application or
interface code, never queries storage and never performs cross-aggregate
checks (e.g. ``Evidence.revision_id == Diagnostic.revision_id``) — those are
application-slice concerns.

Encapsulation rules (frozen by design):

- Internal entities are frozen dataclasses: stable identity, epistemic state
  and lifecycle cannot be reassigned by consumers.
- Aggregate collections are private lists exposed read-only as tuples;
  mutation happens only through aggregate methods.
- ``ClaimLifecycle`` is the historical claim state; ``EffectiveValidation``
  is the *current* freshness of that validation (representation only — no
  freshness engine lives in the domain); ``EpistemicState`` is the nature of
  the claim. VALIDATED != FACT: a hypothesis stays INFERRED when validated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ---------------------------------------------------------------------------
# Domain errors — single specialized ValueError carrying a stable code.
# Codes are contract: invalid_problem_statement, duplicate_internal_identity,
# invalid_epistemic_state, invalid_lifecycle_transition, invalid_causal_link,
# invalid_evidence_relation, invalid_root_cause_designation,
# effective_conclusion_conflict, invalid_version.
# ---------------------------------------------------------------------------


class DiagnosticError(ValueError):
    """Domain invariant violation. ``code`` is the stable semantic name."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        super().__init__(f"{code}: {message}")


def _raise(code: str, message: str) -> None:
    raise DiagnosticError(code, message)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class EpistemicState(str, Enum):
    OBSERVED = "OBSERVED"
    CALCULATED = "CALCULATED"
    INFERRED = "INFERRED"
    PROPOSED = "PROPOSED"
    UNKNOWN = "UNKNOWN"


class ClaimLifecycle(str, Enum):
    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"


CLAIM_LIFECYCLE_TRANSITIONS: dict[ClaimLifecycle, frozenset[ClaimLifecycle]] = {
    ClaimLifecycle.DRAFT: frozenset(
        {ClaimLifecycle.VALIDATED, ClaimLifecycle.REJECTED}
    ),
    ClaimLifecycle.VALIDATED: frozenset({ClaimLifecycle.SUPERSEDED}),
    ClaimLifecycle.REJECTED: frozenset(),
    ClaimLifecycle.SUPERSEDED: frozenset(),
}

# Materialized states (VALIDATED/REJECTED/SUPERSEDED) have no hard-delete
# semantics: there is intentionally no delete operation on this aggregate.


class EvidenceRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    CONTRADICTS = "CONTRADICTS"
    CONTEXTUALIZES = "CONTEXTUALIZES"


class CausalRelation(str, Enum):
    # V1 supports exclusively CONTRIBUTES_TO — never CAUSES.
    CONTRIBUTES_TO = "CONTRIBUTES_TO"


class EffectiveValidation(str, Enum):
    CURRENT = "CURRENT"
    STALE_EVIDENCE = "STALE_EVIDENCE"
    REVALIDATION_REQUIRED = "REVALIDATION_REQUIRED"


class ProvenanceOrigin(str, Enum):
    USER = "USER"
    TEO = "TEO"


class FindingRole(str, Enum):
    SYMPTOM = "SYMPTOM"


# ---------------------------------------------------------------------------
# Value objects / compositions
# ---------------------------------------------------------------------------


def _require_non_empty(value: Any, code: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _raise(code, f"{label} obrigatório e não pode ser vazio.")
    return value.strip()


@dataclass(frozen=True)
class Provenance:
    """Origin metadata only — never authorization, approval or authority."""

    origin: ProvenanceOrigin
    detail: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.origin, ProvenanceOrigin):
            _raise(
                "invalid_epistemic_state",
                f"origem de proveniência inválida: {self.origin!r}.",
            )


@dataclass(frozen=True)
class ProblemStatement:
    """Exactly one per Diagnostic. Non-empty trimmed string is required."""

    text: str

    def __post_init__(self) -> None:
        _require_non_empty(
            self.text, "invalid_problem_statement", "problem_statement"
        )


@dataclass(frozen=True)
class ValidationSnapshot:
    """Minimal historical record of a lifecycle transition."""

    from_lifecycle: ClaimLifecycle | None
    to_lifecycle: ClaimLifecycle
    effective_validation: EffectiveValidation
    note: str | None = None


@dataclass(frozen=True)
class RootCauseDesignation:
    """Designates an existing Hypothesis as root cause — never an entity."""

    hypothesis_id: str

    def __post_init__(self) -> None:
        _require_non_empty(
            self.hypothesis_id,
            "invalid_root_cause_designation",
            "root_cause.hypothesis_id",
        )


# ---------------------------------------------------------------------------
# Internal entities (stable identity; no per-entity repositories by design)
#
# Frozen dataclasses: identity, epistemic state and lifecycle cannot be
# reassigned externally. The aggregate mutates lifecycle/effective state
# internally through object.__setattr__ — the only door to state change.
# ---------------------------------------------------------------------------


def _assert_lifecycle_transition(
    current: ClaimLifecycle,
    target: ClaimLifecycle,
) -> None:
    if target not in CLAIM_LIFECYCLE_TRANSITIONS.get(current, frozenset()):
        _raise(
            "invalid_lifecycle_transition",
            f"transição inválida: {current.value} → {target.value}.",
        )


@dataclass(frozen=True)
class Finding:
    """What was found. A finding is never a cause."""

    finding_id: str
    statement: str
    epistemic_state: EpistemicState = EpistemicState.OBSERVED
    role: FindingRole | None = None
    provenance: Provenance | None = None

    def __post_init__(self) -> None:
        _require_non_empty(
            self.finding_id, "duplicate_internal_identity", "finding_id"
        )
        _require_non_empty(self.statement, "invalid_problem_statement", "statement")
        if self.epistemic_state not in (
            EpistemicState.OBSERVED,
            EpistemicState.CALCULATED,
        ):
            _raise(
                "invalid_epistemic_state",
                "finding admite somente OBSERVED ou CALCULATED.",
            )
        if self.role is not None and not isinstance(self.role, FindingRole):
            _raise(
                "invalid_epistemic_state",
                f"finding role inválido: {self.role!r}.",
            )


@dataclass(frozen=True)
class Hypothesis:
    """Proposed causal explanation. Always INFERRED — even when VALIDATED."""

    hypothesis_id: str
    statement: str
    lifecycle: ClaimLifecycle = ClaimLifecycle.DRAFT
    effective_validation: EffectiveValidation = EffectiveValidation.CURRENT
    provenance: Provenance | None = None
    epistemic_state: EpistemicState = EpistemicState.INFERRED
    validation_history: tuple[ValidationSnapshot, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(
            self.hypothesis_id, "duplicate_internal_identity", "hypothesis_id"
        )
        _require_non_empty(self.statement, "invalid_problem_statement", "statement")
        if self.epistemic_state is not EpistemicState.INFERRED:
            _raise(
                "invalid_epistemic_state",
                "hypothesis é sempre INFERRED; VALIDATED != FACT.",
            )
        if not isinstance(self.lifecycle, ClaimLifecycle):
            _raise("invalid_lifecycle_transition", "lifecycle inválido.")
        if not isinstance(self.effective_validation, EffectiveValidation):
            _raise(
                "invalid_epistemic_state",
                f"effective_validation inválido: {self.effective_validation!r}.",
            )
        object.__setattr__(
            self, "validation_history", tuple(self.validation_history or ())
        )


@dataclass(frozen=True)
class CausalLink:
    """Hypothesis --CONTRIBUTES_TO--> Finding|Hypothesis."""

    link_id: str
    source_hypothesis_id: str
    target_id: str
    relation: CausalRelation = CausalRelation.CONTRIBUTES_TO

    def __post_init__(self) -> None:
        _require_non_empty(self.link_id, "duplicate_internal_identity", "link_id")
        _require_non_empty(
            self.source_hypothesis_id, "invalid_causal_link", "source_hypothesis_id"
        )
        _require_non_empty(self.target_id, "invalid_causal_link", "target_id")
        if self.relation is not CausalRelation.CONTRIBUTES_TO:
            _raise(
                "invalid_causal_link",
                "V1 suporta exclusivamente CONTRIBUTES_TO.",
            )


@dataclass(frozen=True)
class EvidenceLink:
    """Reference to external Evidence owned by the Revision — id only.

    The cross-aggregate check ``Evidence.revision_id == Diagnostic.revision_id``
    is intentionally NOT enforced here; it belongs to the application slice.
    """

    link_id: str
    evidence_id: str
    relation: EvidenceRelation
    target_id: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty(self.link_id, "duplicate_internal_identity", "link_id")
        _require_non_empty(
            self.evidence_id, "invalid_evidence_relation", "evidence_id"
        )
        if not isinstance(self.relation, EvidenceRelation):
            _raise(
                "invalid_evidence_relation",
                f"relação de evidência inválida: {self.relation!r}.",
            )


@dataclass(frozen=True)
class DiagnosticConclusion:
    """Always INFERRED. At most one may be VALIDATED per Diagnostic."""

    conclusion_id: str
    statement: str
    lifecycle: ClaimLifecycle = ClaimLifecycle.DRAFT
    rationale: str | None = None
    hypothesis_ids: tuple[str, ...] = ()
    finding_ids: tuple[str, ...] = ()
    root_cause: RootCauseDesignation | None = None
    provenance: Provenance | None = None
    epistemic_state: EpistemicState = EpistemicState.INFERRED
    validation_history: tuple[ValidationSnapshot, ...] = ()

    def __post_init__(self) -> None:
        _require_non_empty(
            self.conclusion_id, "duplicate_internal_identity", "conclusion_id"
        )
        _require_non_empty(self.statement, "invalid_problem_statement", "statement")
        if self.epistemic_state is not EpistemicState.INFERRED:
            _raise(
                "invalid_epistemic_state",
                "conclusion é sempre INFERRED.",
            )
        if not isinstance(self.lifecycle, ClaimLifecycle):
            _raise("invalid_lifecycle_transition", "lifecycle inválido.")
        object.__setattr__(self, "hypothesis_ids", tuple(self.hypothesis_ids or ()))
        object.__setattr__(self, "finding_ids", tuple(self.finding_ids or ()))
        object.__setattr__(
            self, "validation_history", tuple(self.validation_history or ())
        )


# ---------------------------------------------------------------------------
# Aggregate root
#
# Manual __init__ + __slots__: constructor accepts plain iterables for
# rehydration, stores them in private lists and exposes read-only tuple views.
# There are no setters for identity, statement, provenance or version, and no
# delete operations anywhere — materialized material cannot be hard-deleted.
# ---------------------------------------------------------------------------


class Diagnostic:
    """Aggregate root anchored to exactly one Revision."""

    __slots__ = (
        "_diagnostic_id",
        "_revision_id",
        "_problem_statement",
        "_version",
        "_provenance",
        "_findings",
        "_hypotheses",
        "_causal_links",
        "_evidence_links",
        "_diagnostic_conclusions",
    )

    def __init__(
        self,
        *,
        diagnostic_id: str,
        revision_id: str,
        problem_statement: ProblemStatement,
        version: int = 1,
        findings=(),
        hypotheses=(),
        causal_links=(),
        evidence_links=(),
        diagnostic_conclusions=(),
        provenance: Provenance | None = None,
    ) -> None:
        self._diagnostic_id = _require_non_empty(
            diagnostic_id, "duplicate_internal_identity", "diagnostic_id"
        )
        self._revision_id = _require_non_empty(
            revision_id, "invalid_problem_statement", "revision_id"
        )
        if not isinstance(problem_statement, ProblemStatement):
            _raise(
                "invalid_problem_statement",
                "diagnostic exige exatamente um ProblemStatement.",
            )
        self._problem_statement = problem_statement
        if (
            not isinstance(version, int)
            or isinstance(version, bool)
            or version < 1
        ):
            _raise("invalid_version", "version deve ser inteiro >= 1.")
        self._version = version
        if provenance is not None and not isinstance(provenance, Provenance):
            _raise("invalid_epistemic_state", "provenance inválida.")
        self._provenance = provenance

        self._findings = list(findings)
        self._hypotheses = list(hypotheses)
        self._causal_links = list(causal_links)
        self._evidence_links = list(evidence_links)
        self._diagnostic_conclusions = list(diagnostic_conclusions)

        self._assert_unique_identities()
        for link in self._causal_links:
            self._assert_causal_link(link)
        for link in self._evidence_links:
            self._assert_evidence_link(link)
        for conclusion in self._diagnostic_conclusions:
            self._assert_conclusion_references(conclusion)
        self._assert_single_effective_conclusion()

    # -- read-only views ------------------------------------------------------

    @property
    def diagnostic_id(self) -> str:
        return self._diagnostic_id

    @property
    def revision_id(self) -> str:
        return self._revision_id

    @property
    def problem_statement(self) -> ProblemStatement:
        return self._problem_statement

    @property
    def version(self) -> int:
        return self._version

    @property
    def provenance(self) -> Provenance | None:
        return self._provenance

    @property
    def findings(self) -> tuple[Finding, ...]:
        return tuple(self._findings)

    @property
    def hypotheses(self) -> tuple[Hypothesis, ...]:
        return tuple(self._hypotheses)

    @property
    def causal_links(self) -> tuple[CausalLink, ...]:
        return tuple(self._causal_links)

    @property
    def evidence_links(self) -> tuple[EvidenceLink, ...]:
        return tuple(self._evidence_links)

    @property
    def diagnostic_conclusions(self) -> tuple[DiagnosticConclusion, ...]:
        return tuple(self._diagnostic_conclusions)

    # -- identity / lookup --------------------------------------------------

    def _assert_unique_identities(self) -> None:
        for label, id_attr, items in (
            ("finding", "finding_id", self._findings),
            ("hypothesis", "hypothesis_id", self._hypotheses),
            ("causal_link", "link_id", self._causal_links),
            ("evidence_link", "link_id", self._evidence_links),
            ("conclusion", "conclusion_id", self._diagnostic_conclusions),
        ):
            seen: set[str] = set()
            for item in items:
                item_id = str(getattr(item, id_attr) or "")
                if item_id in seen:
                    _raise(
                        "duplicate_internal_identity",
                        f"{label} id duplicado: {item_id}.",
                    )
                seen.add(item_id)

    def _finding(self, finding_id: str) -> Finding | None:
        return next(
            (f for f in self._findings if f.finding_id == finding_id), None
        )

    def _hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        return next(
            (h for h in self._hypotheses if h.hypothesis_id == hypothesis_id),
            None,
        )

    def _conclusion(self, conclusion_id: str) -> DiagnosticConclusion | None:
        return next(
            (
                c
                for c in self._diagnostic_conclusions
                if c.conclusion_id == conclusion_id
            ),
            None,
        )

    # -- collection mutation -------------------------------------------------

    def add_finding(self, finding: Finding) -> None:
        if self._finding(finding.finding_id):
            _raise(
                "duplicate_internal_identity",
                f"finding_id duplicado: {finding.finding_id}.",
            )
        self._findings.append(finding)

    def add_hypothesis(self, hypothesis: Hypothesis) -> None:
        if self._hypothesis(hypothesis.hypothesis_id):
            _raise(
                "duplicate_internal_identity",
                f"hypothesis_id duplicado: {hypothesis.hypothesis_id}.",
            )
        self._hypotheses.append(hypothesis)

    def _assert_causal_link(self, link: CausalLink) -> None:
        if self._hypothesis(link.source_hypothesis_id) is None:
            _raise(
                "invalid_causal_link",
                f"source inexistente: {link.source_hypothesis_id}.",
            )
        if link.source_hypothesis_id == link.target_id:
            _raise(
                "invalid_causal_link",
                "hypothesis não pode referenciar a si mesma.",
            )
        target_is_finding = self._finding(link.target_id) is not None
        target_is_hypothesis = self._hypothesis(link.target_id) is not None
        if not (target_is_finding or target_is_hypothesis):
            _raise(
                "invalid_causal_link",
                f"target inexistente: {link.target_id}.",
            )

    def add_causal_link(self, link: CausalLink) -> None:
        if any(l.link_id == link.link_id for l in self._causal_links):
            _raise(
                "duplicate_internal_identity",
                f"link_id duplicado: {link.link_id}.",
            )
        self._assert_causal_link(link)
        self._causal_links.append(link)

    def _assert_evidence_link(self, link: EvidenceLink) -> None:
        if link.target_id is not None and not (
            self._finding(link.target_id)
            or self._hypothesis(link.target_id)
            or self._conclusion(link.target_id)
        ):
            _raise(
                "invalid_evidence_relation",
                f"target interno inexistente: {link.target_id}.",
            )

    def add_evidence_link(self, link: EvidenceLink) -> None:
        if any(l.link_id == link.link_id for l in self._evidence_links):
            _raise(
                "duplicate_internal_identity",
                f"link_id duplicado: {link.link_id}.",
            )
        self._assert_evidence_link(link)
        self._evidence_links.append(link)

    # -- lifecycle transitions (historical) ----------------------------------

    @staticmethod
    def _set(claim: Any, name: str, value: Any) -> None:
        """Internal door to frozen-entity state change — aggregate only."""
        object.__setattr__(claim, name, value)

    def _transition_claim(
        self,
        claim: Hypothesis | DiagnosticConclusion,
        target: ClaimLifecycle,
        *,
        note: str | None = None,
    ) -> None:
        _assert_lifecycle_transition(claim.lifecycle, target)
        effective = getattr(
            claim, "effective_validation", EffectiveValidation.CURRENT
        )
        snapshot = ValidationSnapshot(
            from_lifecycle=claim.lifecycle,
            to_lifecycle=target,
            effective_validation=effective,
            note=note,
        )
        self._set(
            claim,
            "validation_history",
            (*claim.validation_history, snapshot),
        )
        self._set(claim, "lifecycle", target)

    def validate_hypothesis(
        self, hypothesis_id: str, *, note: str | None = None
    ) -> None:
        hypothesis = self._require_hypothesis(hypothesis_id)
        self._transition_claim(hypothesis, ClaimLifecycle.VALIDATED, note=note)

    def reject_hypothesis(
        self, hypothesis_id: str, *, note: str | None = None
    ) -> None:
        hypothesis = self._require_hypothesis(hypothesis_id)
        self._transition_claim(hypothesis, ClaimLifecycle.REJECTED, note=note)

    def supersede_hypothesis(
        self, hypothesis_id: str, *, note: str | None = None
    ) -> None:
        hypothesis = self._require_hypothesis(hypothesis_id)
        self._transition_claim(hypothesis, ClaimLifecycle.SUPERSEDED, note=note)

    def _require_hypothesis(self, hypothesis_id: str) -> Hypothesis:
        hypothesis = self._hypothesis(hypothesis_id)
        if hypothesis is None:
            _raise(
                "invalid_causal_link",
                f"hypothesis inexistente: {hypothesis_id}.",
            )
        return hypothesis

    # -- effective validation (representation only) ---------------------------

    def mark_hypothesis_stale_evidence(self, hypothesis_id: str) -> None:
        hypothesis = self._require_hypothesis(hypothesis_id)
        self._set(
            hypothesis, "effective_validation", EffectiveValidation.STALE_EVIDENCE
        )

    def mark_hypothesis_revalidation_required(self, hypothesis_id: str) -> None:
        hypothesis = self._require_hypothesis(hypothesis_id)
        self._set(
            hypothesis,
            "effective_validation",
            EffectiveValidation.REVALIDATION_REQUIRED,
        )

    # -- conclusions -----------------------------------------------------------

    def _assert_conclusion_references(
        self, conclusion: DiagnosticConclusion
    ) -> None:
        for hypothesis_id in conclusion.hypothesis_ids:
            self._require_hypothesis(hypothesis_id)
        for finding_id in conclusion.finding_ids:
            if self._finding(finding_id) is None:
                _raise(
                    "invalid_causal_link",
                    f"finding inexistente: {finding_id}.",
                )
        if conclusion.root_cause is not None:
            designation = conclusion.root_cause
            if self._hypothesis(designation.hypothesis_id) is None:
                _raise(
                    "invalid_root_cause_designation",
                    f"hypothesis inexistente: {designation.hypothesis_id}.",
                )
            if designation.hypothesis_id not in conclusion.hypothesis_ids:
                _raise(
                    "invalid_root_cause_designation",
                    "root cause deve apontar para hypothesis referenciada "
                    "pela conclusão.",
                )

    def _assert_root_cause_effective(
        self, designation: RootCauseDesignation
    ) -> None:
        hypothesis = self._require_hypothesis(designation.hypothesis_id)
        if hypothesis.lifecycle is not ClaimLifecycle.VALIDATED:
            _raise(
                "invalid_root_cause_designation",
                "root cause exige hypothesis VALIDATED.",
            )
        if hypothesis.effective_validation is not EffectiveValidation.CURRENT:
            _raise(
                "invalid_root_cause_designation",
                "root cause exige hypothesis com effective_validation CURRENT.",
            )

    def _validated_conclusion_count(
        self, excluding: DiagnosticConclusion | None = None
    ) -> int:
        return sum(
            1
            for conclusion in self._diagnostic_conclusions
            if conclusion is not excluding
            and conclusion.lifecycle is ClaimLifecycle.VALIDATED
        )

    def _assert_single_effective_conclusion(self) -> None:
        if self._validated_conclusion_count() > 1:
            _raise(
                "effective_conclusion_conflict",
                "mais de uma conclusão VALIDATED neste diagnostic.",
            )

    def add_conclusion(self, conclusion: DiagnosticConclusion) -> None:
        if self._conclusion(conclusion.conclusion_id):
            _raise(
                "duplicate_internal_identity",
                f"conclusion_id duplicado: {conclusion.conclusion_id}.",
            )
        self._assert_conclusion_references(conclusion)
        if (
            conclusion.lifecycle is ClaimLifecycle.VALIDATED
            and self._validated_conclusion_count() > 0
        ):
            _raise(
                "effective_conclusion_conflict",
                "já existe conclusão VALIDATED neste diagnostic.",
            )
        self._diagnostic_conclusions.append(conclusion)

    def _require_conclusion(
        self, conclusion_id: str
    ) -> DiagnosticConclusion:
        conclusion = self._conclusion(conclusion_id)
        if conclusion is None:
            _raise(
                "invalid_causal_link",
                f"conclusion inexistente: {conclusion_id}.",
            )
        return conclusion

    def validate_conclusion(
        self, conclusion_id: str, *, note: str | None = None
    ) -> None:
        conclusion = self._require_conclusion(conclusion_id)
        _assert_lifecycle_transition(
            conclusion.lifecycle, ClaimLifecycle.VALIDATED
        )
        if self._validated_conclusion_count(excluding=conclusion) > 0:
            _raise(
                "effective_conclusion_conflict",
                "já existe conclusão VALIDATED neste diagnostic.",
            )
        if conclusion.root_cause is not None:
            self._assert_root_cause_effective(conclusion.root_cause)
        self._transition_claim(conclusion, ClaimLifecycle.VALIDATED, note=note)

    def reject_conclusion(
        self, conclusion_id: str, *, note: str | None = None
    ) -> None:
        conclusion = self._require_conclusion(conclusion_id)
        self._transition_claim(conclusion, ClaimLifecycle.REJECTED, note=note)

    def supersede_conclusion(
        self, conclusion_id: str, *, note: str | None = None
    ) -> None:
        conclusion = self._require_conclusion(conclusion_id)
        self._transition_claim(conclusion, ClaimLifecycle.SUPERSEDED, note=note)
