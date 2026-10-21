"""CRI E2 — governed outcome-sufficiency assessment.

Bounded deterministic verification applied at the governed-outcome ->
response binding edge (doc 73 §3-§6, spec 75, report 76). A technical
success (HTTP 200 / COMPLETED / provenance present) is never
automatically a task outcome: this module classifies typed evidence
facts into the bounded vocabulary ``answered`` / ``empty_result`` /
``envelope_only`` / ``insufficient`` and validates the semantic
requirements the model *proposed* (as a hypothesis inside the existing
turn-goal stage) against the evidence actually returned.

The assessor receives typed facts only — the orchestrator extracts
records/envelope/completeness with its existing helpers, so this module
stays a leaf: no provider names, no endpoint knowledge, no lexical
intent rules, no model calls.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

# Internal decision vocabulary (doc 73 §6). Logged per turn at the
# binding edge; the wire keeps the existing limitations mechanism —
# sufficiency is represented separately from technical status, never
# by rewriting SUCCESS into an error.
OUTCOME_ANSWERED = "answered"
OUTCOME_EMPTY_RESULT = "empty_result"
OUTCOME_ENVELOPE_ONLY = "envelope_only"
OUTCOME_INSUFFICIENT = "insufficient"

_REQUIREMENT_KEYS = frozenset(
    {"min_items", "ordering", "complete_coverage"}
)
_ORDERINGS = frozenset({"newest_first", "oldest_first"})
MAX_REQUIREMENT_ITEMS = 50
_MAX_ORDERING_FIELD_SCAN = 24


@dataclass(frozen=True, slots=True)
class AnswerRequirements:
    """Typed, model-proposed sufficiency requirements of one turn.

    A hypothesis: the model interprets what the user actually demanded
    (an explicit quantity, a superlative position, full coverage); the
    runtime then verifies each declared requirement against typed
    evidence. Undeclared/absent requirements check nothing — they are
    unproven intent, never defaults invented by the runtime.
    """

    min_items: int | None = None
    ordering: str | None = None
    complete_coverage: bool = False

    @property
    def declared(self) -> bool:
        return (
            self.min_items is not None
            or self.ordering is not None
            or self.complete_coverage
        )


def parse_answer_requirements(value: object) -> AnswerRequirements | None:
    """Validate a proposed ``answer_requirements`` object — fail closed.

    Anything outside the declared contract degrades to ``None`` (no
    requirements checked) rather than being coerced into meaning.
    """

    if value is None:
        return None
    if not isinstance(value, Mapping):
        return None
    if set(value) - _REQUIREMENT_KEYS:
        return None
    min_items = value.get("min_items")
    if min_items is not None and (
        not isinstance(min_items, int)
        or isinstance(min_items, bool)
        or not 1 <= min_items <= MAX_REQUIREMENT_ITEMS
    ):
        return None
    ordering = value.get("ordering")
    if ordering is not None and ordering not in _ORDERINGS:
        return None
    requirements = AnswerRequirements(
        min_items=min_items,
        ordering=ordering,
        complete_coverage=value.get("complete_coverage") is True,
    )
    return requirements if requirements.declared else None


@dataclass(frozen=True, slots=True)
class EvidenceFacts:
    """Typed facts extracted by the orchestrator from a governed
    outcome — bounded projections, never raw payloads.
    """

    records: tuple[Mapping[str, Any], ...] = ()
    has_business_evidence: bool = False
    explicit_empty: bool = False
    is_complete: bool = True
    coverage_complete: bool | None = None
    total_count: int | None = None


@dataclass(frozen=True, slots=True)
class OutcomeVerdict:
    """Sufficiency classification of one governed outcome."""

    decision: str
    reasons: tuple[str, ...] = field(default_factory=tuple)


def _parse_temporal(value: object) -> datetime | None:
    """Bounded ISO temporal parse — strings only.

    Numeric-looking values (ids, years, counters) are never treated as
    dates; that avoids classifying arbitrary ordered numerics as
    temporal ordering evidence.
    """

    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text or len(text) > 40:
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return parsed


def _temporal_order(records: Sequence[Mapping[str, Any]]) -> str | None:
    """Proven uniform temporal ordering across records, if any.

    A direction is proven only when one field carries temporally
    parseable values in every record that declares it (at least two)
    and the sequence is monotonic. Field *names* are never matched —
    the values themselves carry the type evidence.
    """

    if len(records) < 2:
        return None
    keys = sorted(
        {
            key
            for record in records
            for key in record
            if isinstance(key, str)
        }
    )[:_MAX_ORDERING_FIELD_SCAN]
    for key in keys:
        values: list[datetime] = []
        for record in records:
            value = record.get(key)
            if value is None:
                continue
            parsed = _parse_temporal(value)
            if parsed is None:
                values = []
                break
            values.append(parsed)
        if len(values) < 2:
            continue
        if all(a >= b for a, b in zip(values, values[1:])):
            return "newest_first"
        if all(a <= b for a, b in zip(values, values[1:])):
            return "oldest_first"
    return None


def _unproven_requirements(
    facts: EvidenceFacts,
    requirements: AnswerRequirements,
) -> tuple[str, ...]:
    """Requirement-by-requirement verification against typed facts.

    An owner that provably returned fewer items than requested is
    ``fewer_than_requested`` (truthful shortfall); a requirement the
    evidence cannot settle is ``*_unproven`` (honest insufficiency —
    never a fabricated confirmation).
    """

    reasons: list[str] = []
    if requirements.min_items is not None:
        requested = requirements.min_items
        count = len(facts.records)
        if count >= requested or (
            facts.total_count is not None
            and facts.total_count >= requested
        ):
            pass
        elif (
            facts.total_count is not None
            and facts.total_count < requested
        ) or (facts.coverage_complete is True and count < requested):
            reasons.append("fewer_than_requested")
        else:
            reasons.append("quantity_unproven")
    if requirements.ordering is not None:
        order = _temporal_order(facts.records)
        single_complete = (
            len(facts.records) == 1 and facts.coverage_complete is True
        )
        if (
            order == requirements.ordering or single_complete
        ) and facts.coverage_complete is True:
            pass
        elif order == requirements.ordering or single_complete:
            reasons.append("coverage_unproven")
        else:
            reasons.append("ordering_unproven")
    if requirements.complete_coverage and (
        facts.coverage_complete is not True
    ):
        reasons.append("coverage_unproven")
    return tuple(reasons)


def assess_outcome(
    facts: EvidenceFacts,
    requirements: AnswerRequirements | None = None,
) -> OutcomeVerdict:
    """Classify task sufficiency from typed evidence facts.

    ``unavailable`` is classified upstream as SOURCE_UNAVAILABLE and
    never reaches this stage. ``answered`` requires business evidence,
    a complete outcome and every declared requirement proven against
    typed data — anything less degrades honestly.
    """

    if facts.explicit_empty:
        # A proven-empty business collection is a definitive answer —
        # checked before business-evidence presence so an owner text
        # such as "no results" does not hide the empty verdict.
        return OutcomeVerdict(OUTCOME_EMPTY_RESULT)
    if not facts.has_business_evidence:
        return OutcomeVerdict(
            OUTCOME_ENVELOPE_ONLY, ("no_business_data",)
        )
    reasons: list[str] = []
    if not facts.is_complete:
        reasons.append("partial_outcome")
    if requirements is not None and requirements.declared:
        reasons.extend(_unproven_requirements(facts, requirements))
    return OutcomeVerdict(
        OUTCOME_INSUFFICIENT if reasons else OUTCOME_ANSWERED,
        tuple(reasons),
    )
