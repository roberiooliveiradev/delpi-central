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

import json
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
# C3 contextual discovery: a DISCOVERY-class outcome that carries
# owner-published contract data but no business records is a real
# answer about the capability surface — distinct from both business
# evidence and the empty-envelope miss.
OUTCOME_CONTRACT_FACTS = "contract_facts"

_REQUIREMENT_KEYS = frozenset(
    {"min_items", "ordering", "complete_coverage", "ordering_semantic"}
)
_ORDERINGS = frozenset({"newest_first", "oldest_first"})
MAX_REQUIREMENT_ITEMS = 50
_MAX_ORDERING_FIELD_SCAN = 24
_MAX_SEMANTIC_EVIDENCE_LEN = 400

# Bounded event vocabulary — the only business-event meanings the
# presentation vocabulary can express. An event the model names outside
# this set is unverifiable by construction, not coerced.
SEMANTIC_EVENTS = frozenset({"modification"})
_SEMANTIC_KEYS = frozenset({"event", "field", "contract_evidence"})


@dataclass(frozen=True, slots=True)
class OrderingSemantic:
    """Model-proposed event meaning of the required ordering.

    A structured hypothesis only: the model claims the ordering it
    required carries a business event meaning (``event``) proven on a
    specific ``field``, and cites the owner-declared contract text
    (``contract_evidence``) where that meaning is declared. The runtime
    verifies all three deterministically — a proposal is never
    authority by itself.
    """

    event: str
    field: str
    contract_evidence: str


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
    ordering_semantic: OrderingSemantic | None = None

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
    ordering_semantic = _parse_ordering_semantic(
        value.get("ordering_semantic")
    )
    if "ordering_semantic" in value and ordering_semantic is None:
        return None
    if ordering_semantic is not None and ordering is None:
        # A semantic claim attaches to an ordering requirement — a
        # semantic with no ordering is an unverifiable fragment.
        return None
    requirements = AnswerRequirements(
        min_items=min_items,
        ordering=ordering,
        complete_coverage=value.get("complete_coverage") is True,
        ordering_semantic=ordering_semantic,
    )
    return requirements if requirements.declared else None


def _parse_ordering_semantic(value: object) -> OrderingSemantic | None:
    """Structural validation of an ordering-semantic proposal.

    Rejects anything outside the contract rather than coercing it:
    exact keys, bounded event vocabulary, non-empty bounded strings,
    and the claimed field must appear inside the cited evidence — a
    quote that does not even name the field cannot be the declaration
    of that field's meaning.
    """

    if not isinstance(value, Mapping) or set(value) != _SEMANTIC_KEYS:
        return None
    event = value.get("event")
    field = value.get("field")
    evidence = value.get("contract_evidence")
    if event not in SEMANTIC_EVENTS:
        return None
    if (
        not isinstance(field, str)
        or not field
        or len(field) > _MAX_ORDERING_FIELD_SCAN * 4
    ):
        return None
    if (
        not isinstance(evidence, str)
        or not evidence.strip()
        or len(evidence) > _MAX_SEMANTIC_EVIDENCE_LEN
        or field not in evidence
    ):
        return None
    return OrderingSemantic(
        event=event, field=field, contract_evidence=evidence
    )


def verified_ordering_event(
    requirements: AnswerRequirements | None,
    proving_field: str | None,
    owner_contract_text: str | None,
) -> str | None:
    """Verified event meaning of the proven ordering — or None.

    Deterministic verification of the model's semantic hypothesis
    against the owner's own contract text:

    - the proposed ``field`` must be the field that actually proves
      the required ordering in the returned records;
    - the cited ``contract_evidence`` must be a verbatim substring of
      the owner-declared contract text — a fabricated or paraphrased
      quote proves nothing;
    - only then is the bounded ``event`` vocabulary item returned.

    Absence of a proposal, a proving-field mismatch, or a missing/
    unmatched quote all degrade to ``None`` — meaning stays unproven
    and the presentation must say so rather than guess from names.
    """

    semantic = (
        requirements.ordering_semantic if requirements is not None else None
    )
    if (
        semantic is None
        or proving_field is None
        or semantic.field != proving_field
        or not owner_contract_text
        or semantic.contract_evidence not in owner_contract_text
    ):
        return None
    return semantic.event


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
    # Bounded owner-published contract rows ("path: value"), present
    # only for DISCOVERY-class outcomes without business records —
    # capability-surface metadata, never domain facts.
    contract_facts: tuple[str, ...] = ()


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


def _temporal_proofs(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    """Proven uniform temporal orderings — direction -> proving field.

    A direction is proven only when one field carries a temporally
    parseable value in EVERY record — a subset of ordered values inside
    a larger collection never proves ordering (E2-R1). Field *names*
    are never matched — the values themselves carry the type evidence.
    Ties remain monotonic in both directions. The returned map keeps
    the first (sorted) field that proves each direction so the
    presentation edge can quote the proven temporal value verbatim
    (E3-G2) instead of re-deriving it.
    """

    if len(records) < 2:
        return {}
    keys = sorted(
        {
            key
            for record in records
            for key in record
            if isinstance(key, str)
        }
    )[:_MAX_ORDERING_FIELD_SCAN]
    proofs: dict[str, str] = {}
    for key in keys:
        values: list[datetime] = []
        for record in records:
            parsed = _parse_temporal(record.get(key))
            if parsed is None:
                # Missing or non-comparable value in ANY record —
                # this field cannot carry the ordering proof.
                values = []
                break
            values.append(parsed)
        if len(values) != len(records):
            continue
        if all(a >= b for a, b in zip(values, values[1:])):
            proofs.setdefault("newest_first", key)
        if all(a <= b for a, b in zip(values, values[1:])):
            proofs.setdefault("oldest_first", key)
    return proofs


def _temporal_orders(
    records: Sequence[Mapping[str, Any]],
) -> frozenset[str]:
    """Proven uniform temporal orderings across ALL returned records.

    Direction names only — see ``_temporal_proofs`` for the proof
    semantics and the field that carries each proof.
    """

    return frozenset(_temporal_proofs(records))


def ordering_proof_fields(
    records: Sequence[Mapping[str, Any]],
) -> Mapping[str, str]:
    """Direction -> first field that proves the temporal ordering.

    Bounded consumer-facing view of ``_temporal_proofs`` for the
    governed presentation edge: lets the response layer quote the
    proven temporal value verbatim from the extreme record.
    """

    return dict(_temporal_proofs(records))


def parse_temporal_value(value: object) -> datetime | None:
    """Public bounded temporal parse — same semantics as the
    assessment's internal helper; strings only, never coerced."""

    return _parse_temporal(value)


def _distinct_delivered(records: Sequence[Mapping[str, Any]]) -> int:
    """Count of effectively delivered distinct examples (E2-R2).

    Exact-content equality is the only legitimate identity bound —
    never invented identifiers or entity-matching rules. Duplicate
    payloads never inflate the delivered count.
    """

    seen: set[str] = set()
    for record in records:
        try:
            seen.add(json.dumps(record, sort_keys=True, default=str))
        except (TypeError, ValueError):
            seen.add(repr(record))
    return len(seen)


def distinct_delivered_count(
    records: Sequence[Mapping[str, Any]],
) -> int:
    """Public view of ``_distinct_delivered`` for the presentation
    edge — the same exact-content dedup bound, never an invented
    identity."""

    return _distinct_delivered(records)


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
        # E2-R2: the owner's AVAILABLE total never proves the requested
        # examples were DELIVERED — only the distinct records present in
        # this result count as delivery.
        delivered = _distinct_delivered(facts.records)
        if delivered >= requested:
            pass
        elif (
            facts.total_count is not None
            and facts.total_count < requested
        ) or facts.coverage_complete is True:
            reasons.append("fewer_than_requested")
        else:
            reasons.append("quantity_unproven")
    if requirements.ordering is not None:
        orders = _temporal_orders(facts.records)
        single_complete = (
            len(facts.records) == 1 and facts.coverage_complete is True
        )
        order_proven = (
            requirements.ordering in orders or single_complete
        )
        if order_proven and facts.coverage_complete is True:
            pass
        elif order_proven:
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
        if facts.contract_facts:
            # A DISCOVERY-class outcome carrying owner-published
            # contract data is a real answer about the capability
            # surface — but never silently substitutes for declared
            # business requirements: unproven demands ride as reasons
            # so the binding edge marks honest insufficiency while
            # still presenting the published surface.
            reasons: tuple[str, ...] = ()
            if requirements is not None and requirements.declared:
                reasons = _unproven_requirements(
                    facts, requirements
                ) or ("requirements_unproven",)
            return OutcomeVerdict(OUTCOME_CONTRACT_FACTS, reasons)
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
