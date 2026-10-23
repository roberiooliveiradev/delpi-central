"""CRI E2 — governed outcome-sufficiency assessment.

Bounded deterministic verification applied at the governed-outcome ->
response binding edge (doc 73 §3-§6, spec 75, report 76). A technical
success (HTTP 200 / COMPLETED / provenance present) is never
automatically a task outcome: this module classifies typed evidence
facts into the bounded vocabulary ``answered`` / ``empty_result`` /
``envelope_only`` / ``insufficient`` and validates the semantic
requirements the model *proposed* (as a hypothesis inside the existing
turn-goal stage) against the evidence actually returned.

The assessor receives typed facts only — this module also owns the
trusted owner-evidence projection that produces them (R2, plan 125 /
M02-M03): unwrapping owner envelopes, stripping control-plane keys,
redacting sensitive values and normalizing canonical keys, all bounded
and provider-neutral. It stays a leaf: no provider names, no endpoint
knowledge, no lexical intent rules, no model calls — and it never
imports the orchestrator.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Mapping, Sequence

from app.domain.specialist_interop.model import SpecialistOutcome

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
    *,
    contract_subject: bool = False,
) -> OutcomeVerdict:
    """Classify task sufficiency from typed evidence facts.

    ``unavailable`` is classified upstream as SOURCE_UNAVAILABLE and
    never reaches this stage. ``answered`` requires business evidence,
    a complete outcome and every declared requirement proven against
    typed data — anything less degrades honestly.

    ``contract_subject`` is the validated model-declared hypothesis
    that the user asked about the published contract/schema itself.
    Owner contract metadata only substitutes for business evidence
    when that intent was declared — an absent declaration is unproven
    intent and schema rows never answer a business or product-usage
    question (D5 evidence-intent correspondence, doc 124).
    """

    if facts.explicit_empty:
        # A proven-empty business collection is a definitive answer —
        # checked before business-evidence presence so an owner text
        # such as "no results" does not hide the empty verdict.
        return OutcomeVerdict(OUTCOME_EMPTY_RESULT)
    if not facts.has_business_evidence:
        if facts.contract_facts and contract_subject:
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


# ------------------------------------------------------------------
# R2 (plan 125 / M02-M03): trusted owner-evidence projection and
# sanitization — the single trust-projection owner. Every function
# below reduces an UNTRUSTED owner/MCP payload to bounded, safe,
# typed evidence: control-plane keys stripped, sensitive values
# redacted, canonical keys normalized. Model output, catalog data
# and schema metadata remain untrusted here — nothing is promoted
# to business FACT or authority. Moved byte-for-byte from
# orchestration.py; contracts and call shapes unchanged.
# ------------------------------------------------------------------


MAX_SURFACE_ENTRIES = 60


MAX_DESCRIPTION_CHARS = 240


MAX_OWNER_EVIDENCE_CHARS = 12000


MAX_OWNER_EVIDENCE_ENTRY_CHARS = 800


MAX_MISSING_INPUTS = 8


MAX_CANDIDATE_ENTRIES = 10


def _comparison_records(
    outcome: SpecialistOutcome,
) -> tuple[Mapping[str, Any], ...]:
    """Sanitized renderable records of an owner evidence set."""
    return tuple(
        record
        for record in (
            _sanitize_renderable(entity)
            for entity in _resolver_entities(outcome.structured)
        )
        if isinstance(record, Mapping)
    )


def _comparable_scalar(value: object) -> str | None:
    """Normalize a record leaf to a comparable scalar — numbers and
    strings only; anything else is not comparable."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(float(value))
    if isinstance(value, str):
        text = value.strip()
        return text.casefold() if text else None
    return None


def _bound_owner_evidence(outcome: SpecialistOutcome) -> str:
    """Sanitized, size-bounded projection of an owner DISCOVERY result.

    The catalog is untrusted owner data: sensitive keys are redacted,
    it is rendered as data (never instruction), and bounded before
    reaching the argument prompt. Bounding is breadth-first — every
    top-level and second-level entry keeps a bounded row so the whole
    owner vocabulary stays visible; a single deep JSON truncation
    would silently drop the operations the owner actually declares.
    """
    payload = (
        outcome.structured
        if isinstance(outcome.structured, Mapping)
        else outcome.content_text
    )
    if isinstance(payload, str):
        return _redact_text(payload)[:MAX_OWNER_EVIDENCE_CHARS]
    sanitized = _sanitize_renderable(payload)
    compacted = _compact_evidence(sanitized)
    if not isinstance(compacted, Mapping):
        return json.dumps(
            compacted, ensure_ascii=False, default=str
        )[:MAX_OWNER_EVIDENCE_CHARS]

    lines: list[str] = []
    for key, value in list(compacted.items())[:MAX_SURFACE_ENTRIES]:
        _evidence_rows(str(key), value, lines, depth=0)
        if sum(len(line) for line in lines) > MAX_OWNER_EVIDENCE_CHARS:
            break
    return "\n".join(lines)[:MAX_OWNER_EVIDENCE_CHARS]


_EVIDENCE_DROPPED_KEYS = frozenset({"example", "examples"})


MAX_EVIDENCE_SCALAR_LIST = 48


MAX_CONTRACT_FACT_ROWS = 8


MAX_CONTRACT_FACT_ENTITY_ROWS = 4


_CAPABILITY_VOCABULARY_KEYS = frozenset(
    {
        "capabilities",
        "allowedops",
        "operationschemas",
        "operationcatalog",
        "capabilitycatalog",
        "productguide",
        "sideeffecthintcatalog",
        "targetshape",
        "displayformatcatalog",
        "catalogversion",
    }
)


_DISCOVERY_ENVELOPE_KEYS = frozenset(
    {
        "query",
        "topk",
        "candidatecount",
        "eligibleactioncount",
        "candidates",
        "status",
        "success",
        "message",
        "operations",
        "tools",
    }
)


_CAPABILITY_DESCRIPTOR_STRONG_KEYS = frozenset(
    {
        "operationid",
        "whentouse",
        "inputschema",
        "requiresplaylist",
        "sideeffect",
        "sideeffecthint",
        "toolname",
        "toolid",
    }
)


_CAPABILITY_DESCRIPTOR_WEAK_KEYS = frozenset(
    {"op", "operation", "capability", "capabilitykey"}
)


def _is_capability_descriptor(item: object) -> bool:
    """True when a mapping is a capability-catalog descriptor.

    Strong vocabulary fields mark an entry outright when the mapping
    is descriptor-sparse or also carries a weak field; a dense
    business record whose only overlap is a field named ``op`` or
    ``operationId`` stays a business record.
    """
    if not isinstance(item, Mapping):
        return False
    canon = {_canonical_key(key) for key in item}
    strong = canon & _CAPABILITY_DESCRIPTOR_STRONG_KEYS
    weak = canon & _CAPABILITY_DESCRIPTOR_WEAK_KEYS
    if len(weak) >= 2:
        return True
    return bool(strong) and (bool(weak) or len(item) <= 4)


def _without_control_plane(value: Any) -> Any:
    """Drop owner control-plane entries from a projected structure.

    ``agent_directives``/``capability_surface`` are orchestration data
    at any depth — never renderable user content. Recursive on the
    control-plane set only; business fields with homonymous names
    are untouched.
    """
    if isinstance(value, Mapping):
        return {
            key: _without_control_plane(item)
            for key, item in value.items()
            if _canonical_key(key) not in _CONTROL_PLANE_KEYS
        }
    if isinstance(value, (list, tuple)):
        return [_without_control_plane(item) for item in value]
    return value


def _contract_fact_rows(outcome: SpecialistOutcome) -> tuple[str, ...]:
    """Bounded owner-contract digest from a DISCOVERY-class outcome.

    Per-entity contract rows first (the canonical ``entities``
    collection the owner publishes — field/filter vocabulary), then
    one bounded row per remaining top-level section. Breadth-first,
    so a single deep JSON truncation never silently drops the
    vocabulary the owner actually publishes. Same sanitize/redact/
    compact pipeline the argument stage consumes; owner contract
    vocabulary only — control-plane subtrees, capability-catalog
    descriptors and discovery-transport fields are never projected.
    """
    payload = (
        outcome.structured
        if isinstance(outcome.structured, Mapping)
        else outcome.content_text
    )
    if isinstance(payload, str):
        text = payload.strip()
        # A text-only result may itself be a serialized owner payload;
        # JSON object bodies take the structured path so the same
        # exclusions apply instead of line-splitting a raw dump.
        if text.startswith("{"):
            try:
                payload = json.loads(text)
            except (TypeError, ValueError):
                payload = text
        if isinstance(payload, str):
            redacted = _redact_text(payload)
            return tuple(
                line.strip()
                for line in redacted.splitlines()
                if line.strip()
            )[:MAX_CONTRACT_FACT_ROWS]
    sanitized = _sanitize_renderable(_unwrap_owner_payload(payload))
    rows: list[str] = []
    # All entity-contract collections the owner publishes (canonical
    # keys, depth ≤1) — read and write surfaces can coexist in one
    # catalog; the read surface (``capability_surface``) wins name
    # collisions over auxiliary schemas so a write contract is never
    # presented as the READ vocabulary.
    entity_schemas: dict[str, Mapping[str, Any]] = {}
    if isinstance(sanitized, Mapping):
        nested = [
            (key, value)
            for key, value in list(sanitized.items())[
                :MAX_SURFACE_ENTRIES
            ]
            if isinstance(value, Mapping)
        ]
        nested.sort(
            key=lambda kv: _canonical_key(kv[0]) != "capabilitysurface"
        )
        sections = [value for _, value in nested] + [sanitized]
        for section in sections:
            for key, collection in list(section.items())[
                :MAX_SURFACE_ENTRIES
            ]:
                if _canonical_key(key) not in (
                    _ENTITY_SCHEMA_COLLECTION_KEYS
                ):
                    continue
                if isinstance(collection, Mapping):
                    entries: Any = list(collection.items())[
                        :MAX_SURFACE_ENTRIES
                    ]
                elif isinstance(collection, (list, tuple)):
                    # List-form entity contracts (owner publishes
                    # {"id": name, ...schema} entries).
                    entries = (
                        (
                            next(
                                (
                                    item[fk]
                                    for fk in ("id", "name", "entity", "key")
                                    if isinstance(item.get(fk), str)
                                ),
                                None,
                            ),
                            item,
                        )
                        for item in list(collection)[
                            :MAX_SURFACE_ENTRIES
                        ]
                        if isinstance(item, Mapping)
                    )
                else:
                    continue
                for name, schema in entries:
                    if (
                        isinstance(name, str)
                        and isinstance(schema, Mapping)
                        and name not in entity_schemas
                    ):
                        entity_schemas[name] = schema
    for name, schema in list(entity_schemas.items())[
        :MAX_CONTRACT_FACT_ENTITY_ROWS
    ]:
        text = json.dumps(
            _compact_evidence(_without_control_plane(schema)),
            ensure_ascii=False,
            default=str,
        )
        rows.append(
            f"entities.{str(name)[:80]}: "
            f"{text[:MAX_OWNER_EVIDENCE_ENTRY_CHARS]}"
        )
    compacted = _without_control_plane(_compact_evidence(sanitized))
    if not isinstance(compacted, Mapping):
        rows.append(
            json.dumps(compacted, ensure_ascii=False, default=str)[
                :MAX_OWNER_EVIDENCE_ENTRY_CHARS
            ]
        )
        return tuple(rows[:MAX_CONTRACT_FACT_ROWS])
    # Nested sections carry the owner's capability surface; leaf
    # enumerations remain visible after them within the same bound.
    items = list(compacted.items())[:MAX_SURFACE_ENTRIES]
    items.sort(key=lambda kv: not isinstance(kv[1], Mapping))
    entity_collections = frozenset(
        _canonical_key(k) for k in _ENTITY_SCHEMA_COLLECTION_KEYS
    )
    for key, value in items:
        if len(rows) >= MAX_CONTRACT_FACT_ROWS:
            break
        canon = _canonical_key(key)
        if (
            canon in _CONTROL_PLANE_KEYS
            or canon in _CAPABILITY_VOCABULARY_KEYS
            or canon in _DISCOVERY_ENVELOPE_KEYS
            or canon in entity_collections
        ):
            continue
        text = json.dumps(value, ensure_ascii=False, default=str)
        rows.append(
            f"{str(key)[:80]}: {text[:MAX_OWNER_EVIDENCE_ENTRY_CHARS]}"
        )
    return tuple(rows)


# Whitelisted owner-published contract fields of a single discovery
# candidate — identity, declared requirements and the published
# argument schema. Tokens, transport metadata and payloads are never
# projected.
_CANDIDATE_CONTRACT_KEYS = (
    "action_id",
    "entity",
    "description",
    "required_arguments",
    "argument_schema",
)


def _candidate_contract_rows(
    candidate: Mapping[str, Any] | None,
) -> tuple[str, ...]:
    """Bounded contract row for ONE owner-published candidate.

    Relevance is the caller's gate — this projection itself stays
    neutral. Legitimate only when a declared contract goal provably
    bonds this specific candidate's published identity; the same
    sanitize/redact/compact pipeline as ``_contract_fact_rows``
    applies, so credentials, control-plane blobs and oversized
    payloads stay out of user-facing content.
    """
    if not isinstance(candidate, Mapping):
        return ()
    sanitized = _sanitize_renderable(candidate)
    if not isinstance(sanitized, Mapping):
        return ()
    action = sanitized.get("action_id") or sanitized.get("name")
    descriptor = {
        str(key): sanitized[key]
        for key in _CANDIDATE_CONTRACT_KEYS
        if isinstance(key, str)
        and sanitized.get(key) is not None
    }
    if not isinstance(action, str) or not action.strip() or not descriptor:
        return ()
    text = json.dumps(
        _without_control_plane(_compact_evidence(descriptor)),
        ensure_ascii=False,
        default=str,
    )
    return (
        f"candidates.{action.strip()[:80]}: "
        f"{text[:MAX_OWNER_EVIDENCE_ENTRY_CHARS]}",
    )


def _compact_evidence(value: Any, depth: int = 0) -> Any:
    """Deterministic shrink of owner vocabulary before bounding.

    The full catalog must fit the model-input budget, so verbosity is
    removed while every entry stays visible: mappings keep all keys,
    strings are capped, deep lists collapse to a count, and ``example``
    placeholders (owner data the instruction already forbids copying
    verbatim) are dropped entirely.
    """
    if isinstance(value, Mapping):
        return {
            str(k)[:80]: _compact_evidence(v, depth + 1)
            for k, v in list(value.items())[:MAX_SURFACE_ENTRIES]
            if str(k) not in _EVIDENCE_DROPPED_KEYS
        }
    if isinstance(value, (list, tuple)):
        items = list(value)
        # Bounded scalar lists are semantic vocabulary (enums, field
        # names, required flags) — collapsing them to a count would
        # erase the owner-declared values the model needs to build a
        # valid operation. Structured/deep collections still collapse.
        if all(
            not isinstance(item, (Mapping, list, tuple))
            for item in items
        ) and len(items) <= MAX_EVIDENCE_SCALAR_LIST:
            return [
                _compact_evidence(item, depth + 1) for item in items
            ]
        if depth >= 3:
            return f"<{len(items)} items>"
        return [
            _compact_evidence(item, depth + 1)
            for item in items[:MAX_SURFACE_ENTRIES]
        ]
    if isinstance(value, str):
        return value[:MAX_DESCRIPTION_CHARS]
    return value


def _evidence_rows(
    key: str, value: Any, lines: list[str], *, depth: int
) -> None:
    """Flatten mapping/list-of-entries into per-entry bounded rows.

    Large collections fan out so every vocabulary entry keeps a row;
    small or scalar values render inline bounded by the entry cap.
    """
    if isinstance(value, Mapping) and depth < 2 and len(value) > 4:
        children = list(value.items())[:MAX_SURFACE_ENTRIES]
        # The owner operation vocabulary is the primary semantic
        # contract for argument construction — render it ahead of
        # descriptive keys so a budget cut drops prose, never ops.
        children.sort(key=lambda kv: str(kv[0]) != "operations")
        for child_key, child in children:
            _evidence_rows(
                f"{key}.{child_key}", child, lines, depth=depth + 1
            )
        return
    if isinstance(value, (list, tuple)) and depth < 2 and len(value) > 4:
        for index, child in enumerate(list(value)[:MAX_SURFACE_ENTRIES]):
            _evidence_rows(
                f"{key}[{index}]", child, lines, depth=depth + 1
            )
        return
    text = json.dumps(value, ensure_ascii=False, default=str)
    lines.append(f"{key}: {text[:MAX_OWNER_EVIDENCE_ENTRY_CHARS]}")


def _missing_inputs(raw: object) -> tuple[str, ...]:
    """Bounded projection of model-declared missing owner inputs —
    short names only, never values or instructions."""
    if not isinstance(raw, (list, tuple)):
        return ()
    return tuple(
        str(item).strip()[:80]
        for item in list(raw)[:MAX_MISSING_INPUTS]
        if str(item).strip()
    )


_ENTITY_SCHEMA_COLLECTION_KEYS = (
    "entity_schemas",
    "entityschemas",
    "entities",
)


_ENTITY_PAYLOAD_KEYS = ("changes", "payload", "body", "record")


def _extract_owner_entity_schemas(
    structured: object,
) -> Mapping[str, Mapping[str, Any]]:
    """Bounded map of entity_id → owner-published schema fragment."""
    doc = _unwrap_owner_payload(structured)
    if not isinstance(doc, Mapping):
        return {}
    collection: object = None
    for key, value in doc.items():
        if _canonical_key(key) in _ENTITY_SCHEMA_COLLECTION_KEYS:
            collection = value
            break
    if collection is None:
        for value in list(doc.values())[:MAX_SURFACE_ENTRIES]:
            if isinstance(value, Mapping):
                for key, inner in value.items():
                    if _canonical_key(key) in _ENTITY_SCHEMA_COLLECTION_KEYS:
                        collection = inner
                        break
            if collection is not None:
                break
    if not isinstance(collection, Mapping):
        return {}
    out: dict[str, Mapping[str, Any]] = {}
    for name, schema in list(collection.items())[:MAX_SURFACE_ENTRIES]:
        if isinstance(name, str) and isinstance(schema, Mapping):
            out[name] = schema
    return out


def _entity_payload_slot(
    arguments: Mapping[str, Any],
) -> tuple[str | None, str | None, Mapping[str, Any] | None]:
    """Return (entity_id, payload_field, payload_mapping) when present."""
    entity = arguments.get("entity")
    entity_id = (
        str(entity).strip()
        if isinstance(entity, (str, int, float)) and str(entity).strip()
        else None
    )
    for key in _ENTITY_PAYLOAD_KEYS:
        raw = arguments.get(key)
        if isinstance(raw, Mapping):
            return entity_id, key, raw
    return entity_id, None, None


def _value_present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    if isinstance(value, Mapping) and not value:
        return False
    return True


_TECHNICAL_LEAK_MARKERS = (
    "proposal_handle",
    "candidate_token",
    "idempotency",
    "owner_vocabulary",
    "bearer ",
    "tools/list",
    "endpoint",
    "http://",
    "https://",
    "json",
    "schema",
    "mcp",
)


_SNAKE_CASE_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*_[A-Za-z0-9_]+")


MAX_SYNTHESIS_ITEMS = 24


MAX_SYNTHESIS_FIELDS = 6


def _wording_leaks_technical(text: str) -> bool:
    """True when a user-facing string exposes provider/internal
    mechanics — deterministic gate, not a blacklist-only defense."""
    lowered = text.lower()
    if any(marker in lowered for marker in _TECHNICAL_LEAK_MARKERS):
        return True
    if _SNAKE_CASE_TOKEN_RE.search(text):
        return True
    return any(ch in text for ch in "{}[]<>`")


def _synthesis_selections(
    proposal: Mapping[str, Any],
    records: tuple[Mapping[str, Any], ...],
) -> tuple[
    list[tuple[Mapping[str, Any], list[tuple[str, str]]]] | None,
    str,
]:
    """Selection-only parse of a synthesis proposal.

    Returns the selected scalar leaves copied from ``records``, or
    ``(None, reason)``. This is the typed input of a comparison; the
    rendered sentence is not.
    """
    items = proposal.get("items")
    # Adapter historically told models "plain string" values; a JSON
    # array encoded as a string is recovered once, never invented.
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except ValueError:
            return None, "schema_invalid"
    if not isinstance(items, (list, tuple)):
        return None, "schema_invalid"
    if not items:
        return None, "empty_selection"
    selections: list[
        tuple[Mapping[str, Any], list[tuple[str, str]]]
    ] = []
    for item in list(items)[:MAX_SYNTHESIS_ITEMS]:
        if not isinstance(item, Mapping):
            return None, "schema_invalid"
        index = item.get("record_index")
        fields = item.get("fields")
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or not 0 <= index < len(records)
        ):
            return None, "invalid_record_index"
        if not isinstance(fields, (list, tuple)) or not fields:
            return None, "empty_selection"
        record = records[index]
        values: list[tuple[str, str]] = []
        for field_name in list(fields)[:MAX_SYNTHESIS_FIELDS]:
            if not isinstance(field_name, str) or field_name not in record:
                return None, "invalid_field"
            value = record[field_name]
            # An unrenderable leaf (null, object, list or redacted
            # empty) never fails the whole selection — it is skipped;
            # only verbatim scalar owner values reach the user.
            if isinstance(value, (Mapping, list, tuple)) or value is None:
                continue
            rendered_value = _redact_text(str(value).strip())
            if rendered_value:
                values.append((field_name, rendered_value))
        if values:
            selections.append((record, values))
    if not selections:
        return None, "empty_selection"
    return selections, "ok"


_IDENTIFIER_KEYS = frozenset(
    {
        "id",
        "code",
        "codigo",
        "sku",
        "ref",
        "reference",
        "referencia",
        "numero",
        "number",
        "ean",
        "gtin",
    }
)


_IDENTIFIER_PREFIXES = ("codigo", "code", "numero", "number")


_UUID_VALUE_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def _record_identifier(
    record: Mapping[str, Any],
) -> tuple[str, str] | None:
    """The record's own identifier field — verbatim evidence used only
    to anchor the subject of a focused answer, never rendered as a
    clause of its own unless it is the selected field itself.

    Selection ranks a human-readable business code above a surrogate
    UUID: exact identifier keys first, then prefixed/suffixed code
    candidates — and inside each tier a non-UUID value wins; a UUID
    still anchors when nothing better exists.
    """
    scalars = [
        (key, str(value).strip())
        for key, value in record.items()
        if isinstance(value, (str, int, float))
        and not isinstance(value, bool)
        and str(value).strip()
    ]
    for prefer_readable in (True, False):
        for key, text in scalars:
            if _canonical_key(key) in _IDENTIFIER_KEYS and (
                not prefer_readable or not _UUID_VALUE_RE.match(text)
            ):
                return str(key), _redact_text(text)
        for key, text in scalars:
            canon = _canonical_key(key)
            if canon not in _IDENTIFIER_KEYS and (
                canon.endswith("id")
                or canon.endswith("code")
                or canon.startswith(_IDENTIFIER_PREFIXES)
            ) and (
                not prefer_readable or not _UUID_VALUE_RE.match(text)
            ):
                return str(key), _redact_text(text)
    return None


_RESOLVER_ENTITY_KEYS = (
    "candidates",
    "items",
    "results",
    "records",
    "entries",
    "matches",
    "topics",
)


_RESOLVER_ENVELOPE_KEYS = ("data", "result", "payload", "response")


def _unwrap_owner_payload(node: object, depth: int = 0) -> object:
    """Unwrap neutral transport envelopes one level at a time."""
    if depth >= 2 or not isinstance(node, Mapping):
        return node
    inner = next(
        (
            node[key]
            for key in _RESOLVER_ENVELOPE_KEYS
            if isinstance(node.get(key), (Mapping, list, tuple))
        ),
        None,
    )
    return _unwrap_owner_payload(inner, depth + 1) if inner else node


def _resolver_entities(structured: object) -> tuple[Mapping[str, Any], ...]:
    """Bounded candidate entities inside an owner resolver result.

    Shape-agnostic: preferred collection keys first, then the first
    list-of-mappings at bounded depth. Entities carry owner evidence —
    never instructions.
    """
    doc = _unwrap_owner_payload(structured)
    if not isinstance(doc, Mapping):
        return ()

    def _mappings(value: object) -> tuple[Mapping[str, Any], ...]:
        if not isinstance(value, (list, tuple)):
            return ()
        # Capability-catalog descriptors are never owner entities —
        # filtered by descriptor shape, not collection position, so
        # homonymous business fields keep their records eligible.
        return tuple(
            item
            for item in list(value)[:MAX_CANDIDATE_ENTRIES]
            if isinstance(item, Mapping)
            and not _is_capability_descriptor(item)
        )

    for key in _RESOLVER_ENTITY_KEYS:
        entities = _mappings(doc.get(key))
        if entities:
            return entities
    for key, value in list(doc.items())[:MAX_SURFACE_ENTRIES]:
        if _canonical_key(key) in _CAPABILITY_VOCABULARY_KEYS:
            continue
        if isinstance(value, (list, tuple)):
            entities = _mappings(value)
            if entities:
                return entities
        elif isinstance(value, Mapping):
            for key in _RESOLVER_ENTITY_KEYS:
                entities = _mappings(value.get(key))
                if entities:
                    return entities
    return ()


_CONTROL_PLANE_KEYS = frozenset(
    {"agentdirectives", "capabilitysurface"}
)


def _mapping_items_excluding_control(
    node: Mapping[str, Any],
) -> tuple[tuple[str, object], ...]:
    return tuple(
        (str(k), v)
        for k, v in node.items()
        if _canonical_key(k) not in _CONTROL_PLANE_KEYS
    )


_ENVELOPE_SCALAR_KEYS = frozenset(
    {
        "total",
        "totalcount",
        "count",
        "page",
        "pages",
        "pagesize",
        "hasmore",
        "limit",
        "offset",
        "cursor",
        "nextcursor",
    }
)


def _explicit_empty_business_collection(structured: object) -> bool:
    """Proven-empty business collection in a non-paginated payload.

    A list-shaped business payload that is empty is a definitive empty
    result — never inferred from scalars alone. Control-plane and
    envelope keys are excluded from the judgment; a mapping of only
    scalars is a record/envelope, not an empty collection.
    """
    doc = _unwrap_owner_payload(structured)
    if isinstance(doc, (list, tuple)):
        return not doc
    if not isinstance(doc, Mapping):
        return False
    collections = [
        value
        for key, value in doc.items()
        if isinstance(value, (list, tuple))
        and _canonical_key(key) not in _CONTROL_PLANE_KEYS
        and _canonical_key(key) not in _RESOLVER_ENVELOPE_KEYS
    ]
    scalars = [
        value
        for key, value in doc.items()
        if not isinstance(value, (Mapping, list, tuple))
        and value is not None
        and str(value).strip()
        and _canonical_key(key) not in _CONTROL_PLANE_KEYS
        and _canonical_key(key) not in _ENVELOPE_SCALAR_KEYS
    ]
    mappings = [
        key
        for key, value in doc.items()
        if isinstance(value, Mapping)
        and _canonical_key(key) not in _CONTROL_PLANE_KEYS
        and _canonical_key(key) not in _RESOLVER_ENVELOPE_KEYS
    ]
    return (
        bool(collections)
        and all(len(value) == 0 for value in collections)
        and not scalars
        and not mappings
    )


def _prior_supports_typed_attribute_compare(
    records: tuple[Mapping[str, Any], ...],
) -> bool:
    """True when ≥2 prior records share non-excerpt scalar fields.

    Prior DELIA_RESULT text split by ``_prior_excerpt_records`` yields
    only ``excerpt`` leaves — untrusted conversational data, never
    typed owner attributes. Positional string splits are not
    comparability. A compare task may succeed on this path only when
    records already expose shared named scalars under the frozen
    selection-only contract (same grain as ``_proven_field_differences``).
    """
    if len(records) < 2:
        return False
    field_sets: list[set[str]] = []
    for record in records:
        fields = {
            _canonical_key(key)
            for key, value in record.items()
            if _canonical_key(key) != "excerpt"
            and value is not None
            and not isinstance(value, (Mapping, list, tuple))
            and str(value).strip()
        }
        if not fields:
            return False
        field_sets.append(fields)
    shared = set(field_sets[0])
    for other in field_sets[1:]:
        shared &= other
    return bool(shared)


MAX_RENDER_LIST_ITEMS = 50


REDACTION_MARKER = "[REDACTED]"


_SENSITIVE_KEY_NAMES = frozenset(
    {
        "token",
        "candidatetoken",
        "handle",
        "proposalhandle",
        "proposalref",
        "accesstoken",
        "refreshtoken",
        "idtoken",
        "bearertoken",
        "sessiontoken",
        "clientsecret",
        "authorization",
        "password",
        "passwd",
        "apikey",
        "privatekey",
        "credential",
        "credentials",
        "cookie",
        "setcookie",
    }
)


def _canonical_key(name: object) -> str:
    return re.sub(r"[^a-z0-9]", "", str(name).lower())


def _is_sensitive_key(name: object) -> bool:
    return _canonical_key(name) in _SENSITIVE_KEY_NAMES


_TEXT_REDACTIONS = (
    (
        re.compile(
            r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----.*?"
            r"-----END [A-Z0-9 ]*PRIVATE KEY-----",
            re.IGNORECASE | re.DOTALL,
        ),
        REDACTION_MARKER,
    ),
    (
        re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
        "Bearer " + REDACTION_MARKER,
    ),
    (
        re.compile(
            r"(\b(?:authorization|cookie|set-cookie)\s*[:=])\s*"
            r"[^\r\n]+",
            re.IGNORECASE,
        ),
        lambda m: m.group(1) + " " + REDACTION_MARKER,
    ),
    (
        re.compile(
            r"(\b(?:access[-_ ]?token|refresh[-_ ]?token|id[-_ ]?token|"
            r"client[-_ ]?secret|api[-_ ]?key|private[-_ ]?key|"
            r"password|passwd|credential)\b[\"']?\s*[:=]\s*"
            r"[\"']?)[^\s\"',;}]+",
            re.IGNORECASE,
        ),
        lambda m: m.group(1) + REDACTION_MARKER,
    ),
    (
        re.compile(
            r"(\b(?:proposal[-_ ]?handle|handle|candidate[-_ ]?token)\b"
            r"[\"']?\s*[:=]\s*[\"']?)[^\s\"',;}]+",
            re.IGNORECASE,
        ),
        lambda m: m.group(1) + REDACTION_MARKER,
    ),
    (
        re.compile(
            r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"
            r"\.[A-Za-z0-9_-]*\b"
        ),
        REDACTION_MARKER,
    ),
)


def _redact_text(text: object) -> str:
    """Deterministically redact credential material from untrusted
    owner text. Surrounding business content is preserved."""
    if not isinstance(text, str) or not text:
        return ""
    out = text
    for pattern, replacement in _TEXT_REDACTIONS:
        out = pattern.sub(replacement, out)
    return out


def _sanitize_renderable(node: object) -> object:
    """Redact sensitive credential material from rendered structure.

    Remote structured payloads are untrusted data: sensitive keys
    (canonical normalized match) have their values replaced with the
    redaction marker — the key stays so shape is preserved and no
    secret value, length, prefix or hash is exposed. Recurses into
    mappings and bounded lists; candidate_token is covered by the
    canonical set.
    """
    if isinstance(node, Mapping):
        return {
            str(k): (
                REDACTION_MARKER
                if _is_sensitive_key(k)
                else _sanitize_renderable(v)
            )
            for k, v in node.items()
        }
    if isinstance(node, (list, tuple)):
        return [
            _sanitize_renderable(v)
            for v in list(node)[:MAX_RENDER_LIST_ITEMS]
        ]
    if isinstance(node, str):
        # Ordinary key + credential-bearing string value: text
        # redaction still applies — no secret-bearing leaf bypasses.
        return _redact_text(node)
    return node


_GENERIC_COMPLETION_TEXTS = frozenset(
    {"execution completed.", "discovery completed.", "ok", "success"}
)


def _is_generic_status(text: str) -> bool:
    return text.strip().lower() in _GENERIC_COMPLETION_TEXTS
