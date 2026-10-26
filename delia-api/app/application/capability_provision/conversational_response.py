"""CRI E3 — grounded conversational response composition.

Deterministic leaf at the governed-outcome -> response binding edge
(doc 73 §3-§6, spec 75, doc 77 §10 residual E3-G2). Given the E2
sufficiency verdict, typed evidence facts and the governed
presentation vocabulary resource, it composes the response *shape* —
lead, evidence lines, limitation notices, optional continuity — from
sanitized owner values only. It never generates business facts, never
calls a model, never sees provider names or raw payloads:

- selection-only stays frozen (ADR 58): every rendered value is a
  verbatim sanitized owner leaf prepared by the orchestrator;
- the count actually presented is what the content claims (E3-G2) —
  owner totals are quoted only as attributed notices, never as
  delivered examples, and duplicate payloads collapse into one line;
- a truncated list says so, and a presentation shortfall re-marks
  ``insufficient_evidence`` instead of claiming success;
- source shortage is claimed only when the owner's total or proven
  coverage supports it — returned/presented counts never describe
  the source's stock (E3-R1);
- temporal ordering proves order, never meaning — alteration
  language is emitted only for a verified ordering event: a
  model-proposed semantic bound to the proving field and to
  owner-declared contract text (E3-R2, SEMANTIC-INTERPRETATION-01);
- no continuity offer is emitted while no serviceable mechanism
  backs it (E3-R3).

Returning ``None`` degrades to the existing synthesized render —
composition is an enhancement, never a correctness dependency.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from app.application.capability_provision.outcome_assessment import (
    MAX_RENDER_LIST_ITEMS,
    MAX_SYNTHESIS_FIELDS,
    OUTCOME_ANSWERED,
    OUTCOME_CONTRACT_FACTS,
    OUTCOME_EMPTY_RESULT,
    OUTCOME_ENVELOPE_ONLY,
    OUTCOME_INSUFFICIENT,
    AnswerRequirements,
    OutcomeVerdict,
    _CONTROL_PLANE_KEYS,
    _RESOLVER_ENVELOPE_KEYS,
    _UUID_VALUE_RE,
    _canonical_key,
    _record_identifier,
    _sanitize_renderable,
    _synthesis_selections,
    ordering_proof_fields,
    parse_temporal_value,
    verified_ordering_event,
)
from app.application.interaction.contracts import (
    LIMITATION_INSUFFICIENT_EVIDENCE,
    LIMITATION_RESULT_TRUNCATED,
)

MAX_PRESENTED_RECORDS = 5
MAX_FIELDS_PER_RECORD = 4
_MAX_FIELD_SCAN_RECORDS = 32
# Owner-published contract rows are capability-surface metadata —
# bounded in count and per-row size so a large catalog can never
# flood the response.
MAX_CONTRACT_FACT_ROWS = 8
_MAX_CONTRACT_FACT_CHARS = 300

# Reason -> insufficiency vocabulary key, in proximate-cause order:
# the reason closest to what the user actually asked leads the
# honest explanation.
_REASON_MESSAGES = (
    # Semantic relevance reasons lead the proximate-cause ordering:
    # they name WHY the evidence cannot answer (plan 125 adendum).
    ("goal_mismatch", "goal_mismatch"),
    ("relevance_unproven", "relevance_unproven"),
    ("coverage_unproven", "coverage_unproven"),
    ("ordering_unproven", "ordering_unproven"),
    ("fewer_than_requested", "fewer_than_requested"),
    ("quantity_unproven", "quantity_unproven"),
    ("partial_outcome", "partial_outcome"),
    ("no_business_data", "envelope_only"),
)

def _shortage_key(
    *,
    total_count: int | None,
    coverage_complete: bool | None,
    requested: int | None,
) -> str:
    """E3-R1 — pick the shortage message the typed facts support.

    A shortage of the SOURCE is claimable only when the owner's
    authoritative total or proven complete coverage backs it; a bare
    returned/delivered count can never describe the source's stock.
    """

    if (
        total_count is not None
        and requested is not None
        and total_count < requested
    ):
        return "fewer_than_requested_source"
    if coverage_complete is True and total_count is None:
        return "fewer_than_requested_coverage"
    return "fewer_than_requested_returned"


@dataclass(frozen=True, slots=True)
class PresentedRecord:
    """Sanitized, render-ready projection of one owner record.

    Built by the orchestrator (which owns the sanitization helpers);
    this leaf only orders and composes text around the values.
    """

    fields: tuple[tuple[str, str], ...] = ()
    """``(label, rendered_value)`` leaf pairs, presentation order."""
    identifier: str | None = None
    """The record's own identifier value, verbatim — used only to
    anchor a subject sentence."""
    title: str | None = None
    """Best human-readable name/title leaf, verbatim."""


@dataclass(frozen=True, slots=True)
class CriComposition:
    """One composed conversational response."""

    content: str
    presented_records: int
    limitations: tuple[str, ...] = field(default_factory=tuple)


def _format(template: object, **params: object) -> str | None:
    """Bounded template substitution — known placeholders only.

    The vocabulary resource is trusted composition input, but a
    malformed entry degrades the composition to ``None`` instead of
    raising into the response path.
    """

    if not isinstance(template, str) or not template.strip():
        return None
    try:
        return template.format(**params)
    except (KeyError, IndexError, ValueError):
        return None


def _record_line(record: PresentedRecord) -> str | None:
    """One bounded evidence line — `Label: value` pairs inline."""

    fields = record.fields[:MAX_FIELDS_PER_RECORD]
    if not fields:
        if record.identifier:
            return f"- {record.identifier}"
        return None
    return "- " + " · ".join(
        f"{label}: {value}" for label, value in fields
    )


def _subject(record: PresentedRecord) -> str | None:
    """Verbatim anchor for a single-record lead sentence."""

    identifier = record.identifier
    title = record.title
    if identifier and title and title != identifier:
        return f"{identifier} — {title}"
    return identifier or title


def compose_cri_response(
    *,
    verdict: OutcomeVerdict,
    requirements: AnswerRequirements | None,
    records: Sequence[PresentedRecord],
    delivered_count: int,
    total_count: int | None,
    coverage_complete: bool | None,
    ordering_date: str | None,
    ordering_event: str | None,
    vocabulary: Mapping[str, Mapping[str, str]],
    contract_facts: Sequence[str] = (),
    projected_content: str | None = None,
) -> CriComposition | None:
    """Compose the governed conversational response, or ``None``.

    All texts come from the validated declarative vocabulary — this
    function selects *which* template applies by verdict shape and
    substitutes only evidence-derived placeholders.

    ``projected_content`` carries the deterministic governed
    projection already produced for the same outcome (guidance,
    terminal renders). When present it leads the composition — a
    verdict scaffold never displaces content already projected from
    the same evidence.
    """

    leads = vocabulary.get("leads") or {}
    temporal = vocabulary.get("temporal_clauses") or {}
    insufficiency = vocabulary.get("insufficiency") or {}
    labels = vocabulary.get("labels") or {}
    req = requirements or AnswerRequirements()
    params = {
        "identifier": "",
        "date": ordering_date or "",
        "count": "",
        "presented": "",
        "returned": delivered_count,
        "available": total_count if total_count is not None else "",
        "requested": req.min_items if req.min_items is not None else "",
        "delivered": delivered_count,
        "total": total_count if total_count is not None else "",
    }

    # ---- definitive non-answer verdicts ---------------------------
    if verdict.decision == OUTCOME_EMPTY_RESULT:
        text = _format(insufficiency.get("empty_result"), **params)
        return (
            CriComposition(text, 0)
            if text is not None
            else None
        )
    if verdict.decision in (
        OUTCOME_ENVELOPE_ONLY,
        OUTCOME_INSUFFICIENT,
    ):
        key = next(
            (
                message_key
                for reason, message_key in _REASON_MESSAGES
                if reason in verdict.reasons
            ),
            "generic",
        )
        if key == "fewer_than_requested":
            key = _shortage_key(
                total_count=total_count,
                coverage_complete=coverage_complete,
                requested=req.min_items,
            )
        text = _format(insufficiency.get(key), **params)
        return (
            CriComposition(text, 0)
            if text is not None
            else None
        )

    # ---- owner-published contract facts (capability surface) ------
    if verdict.decision == OUTCOME_CONTRACT_FACTS:
        lead = _format(leads.get("contract_facts"), **params)
        if lead is None or not contract_facts:
            return None
        rows = [
            f"- {row[:_MAX_CONTRACT_FACT_CHARS]}"
            for row in contract_facts[:MAX_CONTRACT_FACT_ROWS]
        ]
        content = lead + "\n" + "\n".join(rows)
        projected = (
            projected_content.strip()
            if isinstance(projected_content, str)
            else ""
        )
        if projected:
            content = projected + "\n\n" + content
        return CriComposition(content, len(rows))

    if verdict.decision != OUTCOME_ANSWERED or not records:
        return None

    # ---- answered: ordering extreme (single focused record) -------
    paragraphs: list[str] = []
    limitations: list[str] = []
    presented = 0
    record_lines: list[str] = []
    ordering = req.ordering
    if ordering in ("newest_first", "oldest_first"):
        subject = _subject(records[0])
        # E3-R2 / SEMANTIC-INTERPRETATION-01: ordering proves ORDER
        # only. Alteration wording is allowed solely when the proven
        # ordering carries a verified event meaning — a model-proposed,
        # owner-contract-verified semantic, never a field-name guess;
        # otherwise the wording is neutral and states the meaning is
        # unproven.
        modified = ordering_event == "modification"
        lead_key = (
            "ordering_newest_single_modified"
            if ordering == "newest_first" and modified
            else "ordering_newest_single_neutral"
            if ordering == "newest_first"
            else "ordering_oldest_single"
        )
        if subject is not None:
            lead = _format(
                leads.get(lead_key), **{**params, "identifier": subject}
            )
            if lead is None:
                return None
            paragraphs.append(lead)
            if ordering_date:
                clause = _format(
                    temporal.get(
                        f"{ordering}_modified" if modified
                        else f"{ordering}_neutral"
                    ),
                    **params,
                )
                if clause is None:
                    return None
                paragraphs.append(clause)
            presented = 1
            return CriComposition(
                "\n\n".join(paragraphs), presented, tuple(limitations)
            )

    # ---- answered: requested quantity of examples -----------------
    seen_lines: set[str] = set()
    if req.min_items is not None:
        target = min(req.min_items, len(records))
        record_lines = []
        for record in records[:_MAX_FIELD_SCAN_RECORDS]:
            if len(record_lines) >= min(target, MAX_PRESENTED_RECORDS):
                break
            line = _record_line(record)
            if line is None or line in seen_lines:
                continue
            seen_lines.add(line)
            record_lines.append(line)
        presented = len(record_lines)
        if not record_lines:
            return None
        lead = _format(
            leads.get("examples_fulfilled"),
            **{**params, "count": presented},
        )
        if lead is None:
            return None
        paragraphs.append(lead)
        paragraphs.append("\n".join(record_lines))
    elif len(records) == 1:
        record = records[0]
        if not record.fields:
            return None
        lead = _format(leads.get("single_found"), **params)
        if lead is None:
            return None
        paragraphs.append(lead)
        paragraphs.append(
            "\n".join(
                f"- {label}: {value}"
                for label, value in record.fields[:MAX_FIELDS_PER_RECORD]
            )
        )
        presented = 1
    else:
        for record in records[:MAX_PRESENTED_RECORDS]:
            line = _record_line(record)
            if line is None or line in seen_lines:
                continue
            seen_lines.add(line)
            record_lines.append(line)
        presented = len(record_lines)
        if not record_lines:
            return None
        lead = _format(
            leads.get("records_found"),
            **{**params, "count": delivered_count},
        )
        if lead is None:
            return None
        paragraphs.append(lead)
        paragraphs.append("\n".join(record_lines))

    # ---- presentation-faithfulness notices (E3-G2) -----------------
    # ``delivered_count`` is the canonical distinct-delivered figure
    # (same source as the lead) — ``records`` is the scan-capped
    # projection and must never surface as a user-facing count.
    if presented < delivered_count:
        notice = _format(
            labels.get("truncation_notice"),
            **{**params, "presented": presented},
        )
        if notice is not None:
            paragraphs.append(notice)
        if LIMITATION_RESULT_TRUNCATED not in limitations:
            limitations.append(LIMITATION_RESULT_TRUNCATED)
    elif coverage_complete is False:
        if total_count is not None and total_count > len(records):
            notice = _format(
                labels.get("available_notice"), **params
            )
        else:
            notice = _format(labels.get("more_available"), **params)
        if notice is not None:
            paragraphs.append(notice)

    # A request the projection could not fully present re-marks
    # insufficiency — the count claim never exceeds what was rendered.
    if req.min_items is not None and presented < req.min_items:
        if LIMITATION_INSUFFICIENT_EVIDENCE not in limitations:
            limitations.append(LIMITATION_INSUFFICIENT_EVIDENCE)

    # E3-R3: no continuity offer is emitted — the governed contracts
    # carry no serviceable mechanism (no expandable-detail block, no
    # proven next-turn retrieval binding), so promising detail would
    # offer a capability that cannot be served.

    return CriComposition(
        "\n\n".join(paragraphs), presented, tuple(limitations)
    )


# ------------------------------------------------------------------
# Field-label resolution (C3-S3 / RQ-SA05 / D8)
#
# Single governed projection for owner field names across every
# presentation path — detail lines, focused-answer clauses, CRI
# presented records and comparisons. The vocabulary itself lives in
# the versioned ``cri_presentation`` resource (``field_labels``
# section); this module is the only resolver, so CRI and baseline
# paths can never diverge.
#
# A key absent from the governed map is *unknown*: the owner wording
# is preserved verbatim — words humanize (underscores become
# spaces), digit-bearing code-shaped keys stay byte-exact. A field
# name is never translated nor merged (``codigo_processo`` must
# never render as ``Codigoprocesso`` or an invented meaning).

FieldLabels = Mapping[str, tuple[str, str, str]]
"""Canonical field key → (article, label, suffix) parts."""


def field_label_parts(
    canon: str,
    field_labels: FieldLabels | None,
) -> tuple[str, str, str] | None:
    """Governed label parts for a canonicalized key, or ``None``."""
    if field_labels:
        return field_labels.get(canon)
    return None


def unmapped_field_label(key: object, *, capitalized: bool = True) -> str:
    """Presentation label for a field absent from the governed map.

    Digit-bearing keys are code-shaped identifiers (``b2_cm1``) and
    stay byte-exact — mangling corrupts a searchable business code.
    Word keys humanize: the owner's words are preserved verbatim,
    only underscores become spaces — a label is never translated.
    """
    raw = str(key).strip()
    if not raw or any(ch.isdigit() for ch in raw):
        return raw
    spaced = raw.replace("_", " ").strip()
    if not capitalized:
        return spaced
    return spaced[:1].upper() + spaced[1:]


def field_display_label(
    canon: str,
    raw_key: object,
    field_labels: FieldLabels | None = None,
) -> str:
    """Title-case label for detail/record rendering — governed label
    or neutral fallback. First-char casing only, so acronym labels
    (``CNPJ``, ``SKU``) keep their canonical form."""
    parts = field_label_parts(canon, field_labels)
    if parts is not None:
        return parts[1][:1].upper() + parts[1][1:]
    return unmapped_field_label(raw_key)


def field_clause_label(
    canon: str,
    raw_key: object,
    field_labels: FieldLabels | None = None,
) -> str:
    """Bounded pt-BR subject for one selected field — governed
    ``article label suffix`` or the neutral ``o campo "…"`` clause."""
    parts = field_label_parts(canon, field_labels)
    if parts is not None:
        article, label, participle = parts
        return f"{article} {label} {participle}"
    return f'o campo "{unmapped_field_label(raw_key, capitalized=False)}"'


# ------------------------------------------------------------------
# CRI presentation projection (R3/M05, plan 125). Record rendering
# and ordering presentation moved from orchestration.py: the
# composition owner now prepares PresentedRecord triples, scalar
# leaf rendering and ordering date/event from typed evidence —
# activation flags, call ledger and logging stay in coordinator
# glue.
# ------------------------------------------------------------------

MAX_PRESENTED_VALUE_CHARS = 140

# Structural citation coordinates inside owner records (line/page
# ranges, chunk indices, sanitize flags) — provenance metadata, not
# the substantive content the user asked for. They stay renderable
# but sort below every ordinary field so the bounded per-record line
# spends its field budget on content first.
_PRESENTATION_CITATION_KEYS = frozenset(
    {
        "linestart",
        "lineend",
        "chunk",
        "chunkindex",
        "offset",
        "position",
        "pagerange",
        "pagestart",
        "pageend",
        "sanitized",
    }
)


def records_are_prior_excerpts(
    records: tuple[Mapping, ...] | list[Mapping],
) -> bool:
    """True when every record is a prior-turn excerpt leaf only."""
    if not records:
        return False
    return all(
        isinstance(record, Mapping)
        and bool(record)
        and all(
            _canonical_key(str(key)) == "excerpt" for key in record
        )
        for record in records
    )


def cri_scalar_text(value: object) -> str | None:
    """Render one owner leaf for CRI presentation — verbatim
    values, pt-BR readable booleans/dates, bounded."""
    if isinstance(value, bool):
        return "sim" if value else "não"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        parsed = parse_temporal_value(text)
        if parsed is not None:
            base = parsed.strftime("%d/%m/%Y")
            if (
                parsed.hour
                or parsed.minute
                or parsed.second
                or parsed.microsecond
            ):
                return f"{base} às {parsed.strftime('%Hh%M')}"
            return base
        return text
    return None


def presented_record(
    record: Mapping,
    field_labels: FieldLabels | None = None,
) -> PresentedRecord:
    """Sanitized render-ready projection of one owner record.

    Scalars only — nested payloads stay out of the natural line
    and remain reachable through the existing detail paths. Field
    order is presentational: identifier first, then name/title,
    then the rest in owner order. All values are verbatim
    sanitized leaves — selection-only stays frozen.
    """
    sanitized = _sanitize_renderable(record)
    if not isinstance(sanitized, Mapping):
        return PresentedRecord()
    triples: list[tuple[str, str, str]] = []
    for key, value in sanitized.items():
        rendered = cri_scalar_text(value)
        if rendered is None:
            continue
        canon = _canonical_key(key)
        # UUID leaves are surrogate references, never
        # user-meaningful content — a record's identity is
        # anchored by the business identifier/title; an opaque
        # UUID under any field name adds nothing.
        if _UUID_VALUE_RE.match(rendered):
            continue
        label = field_display_label(canon, key, field_labels)
        triples.append(
            (canon, label, rendered[:MAX_PRESENTED_VALUE_CHARS])
        )
    identifier = _record_identifier(record)
    id_canon = (
        _canonical_key(identifier[0]) if identifier else None
    )
    name_keys = {
        "nome",
        "name",
        "titulo",
        "title",
        "descricao",
        "description",
    }

    def _is_name(canon: str) -> bool:
        return canon in name_keys or canon.startswith(
            tuple(name_keys)
        )

    triples.sort(
        key=lambda item: (
            0
            if item[0] == id_canon
            else 1
            if _is_name(item[0])
            else 3
            if item[0] in _PRESENTATION_CITATION_KEYS
            else 2
        )
    )
    by_key = {canon: rendered for canon, _, rendered in triples}
    title = next(
        (
            rendered
            for canon, _, rendered in triples
            if _is_name(canon) and canon != id_canon
        ),
        None,
    )
    return PresentedRecord(
        fields=tuple(
            (label, rendered) for _, label, rendered in triples
        ),
        identifier=(
            by_key.get(id_canon, identifier[1])
            if id_canon is not None
            else None
        ),
        title=title,
    )


def ordering_presentation(
    records: Sequence[Mapping],
    verdict: OutcomeVerdict,
    requirements: AnswerRequirements | None,
    contract_text: str | None = None,
) -> tuple[str | None, str | None]:
    """Bounded ordering date/event for the CRI composition.

    SEMANTIC-INTERPRETATION-01: the model may propose the
    ordering's event meaning; it is claimed only after the
    deterministic check binds the proposal to the field that
    actually proves the ordering AND to owner-declared contract
    text.
    """
    ordering_date = None
    ordering_event = None
    if (
        verdict.decision == OUTCOME_ANSWERED
        and requirements is not None
        and requirements.ordering
        and records
    ):
        ordering_field = ordering_proof_fields(records).get(
            requirements.ordering
        )
        ordering_event = verified_ordering_event(
            requirements, ordering_field, contract_text
        )
        raw = (
            records[0].get(ordering_field)
            if ordering_field is not None
            else None
        )
        if raw is None and len(records) == 1:
            raw = next(
                (
                    value
                    for value in records[0].values()
                    if parse_temporal_value(value) is not None
                ),
                None,
            )
        if parse_temporal_value(raw) is not None:
            ordering_date = cri_scalar_text(raw)
    return ordering_date, ordering_event


# ------------------------------------------------------------------
# M06/R4 — deterministic presentation helpers relocated from the
# orchestration coordinator (plan 125): pure format/projection
# ownership — no capability execution, no provider access, no
# authorization decisions. Behavior is byte-parity, not rewritten.
# ------------------------------------------------------------------

MAX_RENDER_CONTENT_CHARS = 2000

def _render_synthesis(
    proposal: Mapping[str, Any],
    records: tuple[Mapping[str, Any], ...],
    *,
    has_more: bool | None = None,
    projected_omitted: int = 0,
    field_labels: FieldLabels | None = None,
) -> tuple[str | None, str]:
    """Deterministic render of an evidence-bound synthesis proposal.

    The contract is selection-only: there is no model-authored prose
    channel, so no model text can ever introduce a factual leaf value.
    Every rendered value is copied verbatim from the sanitized
    records — invalid indices, unknown fields, empty selections or
    non-scalar values reject the whole proposal. The bounded rejection
    reason code is returned for observability (LOOP-03R2A) — never
    proposal content.

    The optional ``presentation`` field carries a closed vocabulary
    hint (``answer`` | ``list`` | ``detail``); anything outside it is
    ignored and the runtime derives a safe projection — a single
    selected record composes a focused grounded sentence, several
    records compose a bounded introduced list.

    ``has_more`` (R5) prevents page-slice length from being framed as
    an authoritative total when the owner reports more pages.
    ``projected_omitted`` (C3-B) is the count of owner records dropped
    from the model-visible projection — the rendered list is then
    introduced as partial, never as the complete owner result.
    Presentation does not decide whether a comparison succeeded.
    """
    selections, reason = _synthesis_selections(proposal, records)
    if selections is None:
        return None, reason
    mode = proposal.get("presentation")
    if mode not in _PRESENTATION_INTENTS:
        mode = "answer" if len(selections) == 1 else "list"
    if mode == "detail":
        lines: list[str] = []
        for record, values in selections:
            lines.append(_detail_header(record))
            lines.extend(
                _detail_lines(values, field_labels=field_labels)
            )
        return "\n".join(lines)[:MAX_RENDER_CONTENT_CHARS], "rendered"
    if mode == "list" or (
        len(selections) > 1 and mode != "answer"
    ):
        selected_records = tuple(record for record, _ in selections)
        lines = [
            _list_header(
                len(selections),
                records=selected_records,
                has_more=has_more,
                projected_omitted=projected_omitted,
            )
        ]
        for _record, values in selections:
            rendered = " — ".join(value for _, value in values).strip()
            # A prior excerpt may already be a list item. Do not nest
            # a second marker in front of it.
            if re.match(r"^(?:[-*]|\d+[.)])\s+\S", rendered):
                lines.append(rendered)
            else:
                lines.append(f"- {rendered}")
        return "\n".join(lines)[:MAX_RENDER_CONTENT_CHARS], "rendered"
    if len(selections) == 2 and mode == "answer":
        # Stage 05: two focused selections → grounded sentences plus
        # deterministic field diffs from owner scalars only.
        left_record, left_values = selections[0]
        right_record, right_values = selections[1]
        lines = [
            _compose_answer(
                left_record, left_values, field_labels=field_labels
            ),
            _compose_answer(
                right_record, right_values, field_labels=field_labels
            ),
        ]
        diff = _proven_field_differences(
            left_values, right_values, field_labels=field_labels
        )
        if diff:
            lines.append("Diferenças comprovadas:")
            lines.extend(diff)
        return "\n".join(lines)[:MAX_RENDER_CONTENT_CHARS], "rendered"
    record, values = selections[0]
    return (
        _compose_answer(record, values, field_labels=field_labels)[
            :MAX_RENDER_CONTENT_CHARS
        ],
        "rendered",
    )

def _proven_field_differences(
    left_values: list[tuple[str, str]],
    right_values: list[tuple[str, str]],
    *,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    """Deterministic diffs of selected scalar fields present on both sides.

    Synthetic prior-turn ``excerpt`` leaves are session prose, not owner
    registry fields — they are omitted from the diff section so the
    technical field name never surfaces (R-S05-01).
    """
    right_map = {name: value for name, value in right_values}
    lines: list[str] = []
    for name, left_value in left_values:
        if _canonical_key(name) == "excerpt":
            continue
        right_value = right_map.get(name)
        if right_value is None or right_value == left_value:
            continue
        label = field_display_label(
            _canonical_key(name), name, field_labels
        )
        lines.append(f"- {label}: {left_value} → {right_value}")
    return lines[:MAX_SYNTHESIS_FIELDS]

def _selected_proven_differences(
    proposal: Mapping[str, Any] | None,
    records: tuple[Mapping[str, Any], ...],
    *,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    """Typed field diffs for a two-record selection.

    Empty when the proposal does not select exactly two records or
    when shared scalars do not differ. A rendered heading is not an
    input and is not proof.
    """
    if not isinstance(proposal, Mapping):
        return []
    selections, reason = _synthesis_selections(proposal, records)
    if reason != "ok" or not selections or len(selections) != 2:
        return []
    return _proven_field_differences(
        selections[0][1], selections[1][1], field_labels=field_labels
    )

_INSUFFICIENCY_CONTENT = (
    "Com as evidências disponíveis não consigo responder a esse "
    "pedido de forma fundamentada. O que a fonte retornou não "
    "sustenta a conclusão pedida — não invento dados para completar "
    "a resposta."
)

def _insufficiency_content() -> str:
    """Bounded honest limitation when synthesis selects no evidence."""
    return _INSUFFICIENCY_CONTENT[:MAX_RENDER_CONTENT_CHARS]

# Closed presentation vocabulary for the synthesis contract — a
# bounded hint, never prose; anything outside it is derived
# deterministically by the runtime.
_PRESENTATION_INTENTS = frozenset({"answer", "list", "detail"})

def _compose_answer(
    record: Mapping[str, Any],
    values: list[tuple[str, str]],
    *,
    field_labels: FieldLabels | None = None,
) -> str:
    """One focused grounded sentence for a single selected record.

    The record's own identifier anchors the subject (``do registro
    <id>``) — copied verbatim, never invented; when the identifier
    field itself is the selected field it renders as the clause
    instead of the subject.

    Prior-turn continuity records use a synthetic ``excerpt`` leaf.
    Those values are session evidence already phrased for the user —
    render them directly instead of the technical
    ``O campo "excerpt" é:`` wrapper (R-S05-01).
    """
    if values and all(
        _canonical_key(field_name) == "excerpt" for field_name, _ in values
    ):
        text = " ".join(value for _, value in values).strip()
        if not text:
            return ""
        if text.endswith((".", "!", "?")):
            sentence = text
        else:
            sentence = text + "."
        return sentence[:1].upper() + sentence[1:]

    identifier = _record_identifier(record)
    id_field, id_value = identifier if identifier else (None, None)
    subject = f" do registro {id_value}" if id_value else ""
    clauses = [(f, v) for f, v in values if f != id_field]
    if not clauses:
        clauses = list(values)
        subject = ""
    parts = [
        f"{field_clause_label(_canonical_key(field_name), field_name, field_labels)}"
        f" é: {value}"
        for field_name, value in clauses
    ]
    first, *rest = parts
    sentence = first.replace(" é:", subject + " é:", 1)
    if rest:
        sentence += "; " + "; ".join(rest)
    return sentence[:1].upper() + sentence[1:] + "."

def _detail_header(record: Mapping[str, Any]) -> str:
    identifier = _record_identifier(record)
    if identifier:
        return f"Detalhes do registro {identifier[1]}:"
    # Prior-turn excerpts are not owner registry rows — avoid the
    # technical "registro" framing when every leaf is an excerpt.
    if record and all(
        _canonical_key(str(key)) == "excerpt" for key in record
    ):
        return "Trechos anteriores:"
    return "Detalhes do registro:"

def _detail_lines(
    values: list[tuple[str, str]],
    *,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    lines = []
    for field_name, value in values:
        if _canonical_key(field_name) == "excerpt":
            # Presentation-only: do not expose the synthetic field name.
            # Keep a marker the excerpt already has; do not nest another.
            text = value.strip()
            if re.match(r"^(?:[-*]|\d+[.)])\s+\S", text):
                lines.append(text)
            else:
                lines.append(f"- {text}")
            continue
        label = field_display_label(
            _canonical_key(field_name), field_name, field_labels
        )
        lines.append(f"- {label}: {value}")
    return lines

def _list_header(
    count: int,
    *,
    records: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]] | None = None,
    has_more: bool | None = None,
    projected_omitted: int = 0,
) -> str:
    """Bounded list introduction — outcome-aware (doc 35 R3 + R5).

    When the owner page reports ``has_more=True``, the returned item
    count is a page slice — never presented as an authoritative total.
    ``projected_omitted`` marks owner records that stayed out of the
    model-visible projection: the list is then introduced as partial,
    never as the complete owner result.
    """
    if records is not None and records_are_prior_excerpts(records):
        noun = "itens" if count != 1 else "item"
        return f"Recuperei {count} {noun} da orientação anterior:"
    if has_more is True:
        return (
            f"Mostrando {count} registro(s) nesta página; há mais "
            f"resultados além desta página — este número não é o total."
        )
    if projected_omitted > 0:
        return (
            f"Mostrando {count} registro(s); a fonte retornou mais "
            f"resultados que não foram apresentados — esta lista "
            f"não é exaustiva."
        )
    noun = "registros" if count != 1 else "registro"
    return f"Encontrei {count} {noun}:"

# Bounded set of known transport-level completion texts — suppressed
# only when authoritative business data is rendered instead. Arbitrary
# owner text is never suppressed.
EMPTY_RESULT_TEXT = "Nenhum resultado encontrado."

_ITEMS_KEY = "items"

def _format_structured(
    node: object,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    """Deterministic human-readable projection of owner data.

    Formats bounded sanitized structures into key/value lines and list
    items — formatting only: no inference, no semantic renaming, no
    computed values. Returns [] when the node is not formattable so
    the caller may fall back to a bounded JSON dump.
    """
    indent = "  " * depth
    if depth > 3:
        return []
    if isinstance(node, Mapping):
        lines: list[str] = []
        for key, value in node.items():
            key = str(key)
            canon = _canonical_key(key)
            # Owner control-plane metadata (agent directives, the
            # capability surface) is orchestration data — never
            # projected into the user-facing answer.
            if canon in _CONTROL_PLANE_KEYS:
                continue
            display = (
                field_display_label(canon, key, field_labels)
                if field_labels is not None
                else key
            )
            if isinstance(value, Mapping):
                sub = _format_structured(
                    value, depth + 1, field_labels=field_labels
                )
                lines.append(f"{indent}{display}:")
                lines.extend(sub or [f"{indent}  {{}}"])
            elif isinstance(value, (list, tuple)):
                items = list(value)[:MAX_RENDER_LIST_ITEMS]
                if items:
                    lines.append(f"{indent}{display}:")
                    lines.extend(
                        _format_list(
                            items, depth + 1, field_labels=field_labels
                        )
                    )
                else:
                    lines.append(f"{indent}{display}: (vazio)")
            else:
                if value is None:
                    continue
                lines.append(f"{indent}{display}: {value}")
        return lines
    return []

def _format_list(
    items: list,
    depth: int,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    indent = "  " * depth
    lines: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            first = True
            for key, value in item.items():
                canon = _canonical_key(key)
                if canon in _CONTROL_PLANE_KEYS:
                    continue
                if isinstance(value, (Mapping, list, tuple)) or value is None:
                    continue
                display = (
                    field_display_label(canon, key, field_labels)
                    if field_labels is not None
                    else key
                )
                prefix = "- " if first else "  "
                lines.append(
                    f"{indent}{prefix}{display}: {value}"
                )
                first = False
            if first:
                lines.append(f"{indent}- {{}}")
        elif isinstance(item, (list, tuple)):
            return []
        else:
            lines.append(f"{indent}- {item}")
    return lines

def _format_records(
    items: list,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    """Bounded numbered record list for multi-item business payloads."""
    indent = "  " * depth
    lines: list[str] = []
    for idx, item in enumerate(items, 1):
        if isinstance(item, Mapping):
            lines.append(f"{indent}{idx}.")
            lines.extend(
                _format_structured(
                    item, depth + 1, field_labels=field_labels
                )
                or [f"{indent}  {{}}"]
            )
        else:
            lines.append(f"{indent}{idx}. {item}")
    return lines

def _business_lines(
    node: Mapping,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> list[str] | None:
    """Project the authoritative business payload for user display.

    Owners commonly wrap business data in technical envelopes: a
    ``data``/``result``/``payload``/``response`` member carries the
    payload while siblings carry transport/pagination metadata that
    must not dominate the primary answer. Unwrapping is structural,
    recursive and bounded — never a per-specialist or per-action
    branch. Returns ``None`` for unrecognized shapes so the caller
    can fall back to the generic sanitized render.
    """
    if depth > 2:
        return None
    for key in _RESOLVER_ENVELOPE_KEYS:
        payload = node.get(key)
        if isinstance(payload, Mapping):
            items = payload.get(_ITEMS_KEY)
            if isinstance(items, list):
                if not items:
                    return [EMPTY_RESULT_TEXT]
                if len(items) == 1 and isinstance(items[0], Mapping):
                    return (
                        _format_structured(
                            items[0], field_labels=field_labels
                        )
                        or None
                    )
                return _format_records(
                    items, field_labels=field_labels
                )
            nested = _business_lines(
                payload, depth + 1, field_labels=field_labels
            )
            if nested is not None:
                return nested
            return (
                _format_structured(payload, field_labels=field_labels)
                or None
            )
        if isinstance(payload, list):
            if not payload:
                return [EMPTY_RESULT_TEXT]
            return _format_records(payload, field_labels=field_labels)
    return None

# G3-RW-01: a leaf must remain literal data — the projector owns every
# structural decision. ALL CommonMark-escapable ASCII punctuation is
# backslash-escaped so owner text can never form emphasis, code spans,
# links, autolinks (bare URL/email/www — verified against marked: only
# escaping the scheme colon breaks GFM autolink detection), inline HTML
# or entity references. Escaped punctuation renders identically, so
# business values display verbatim.
_MD_ESCAPABLE = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"

# CR/LF/CRLF and the Unicode line/paragraph separators inside owner
# data normalize to a plain space — the leaf stays on the line the
# projector emitted and `# `/`- `/`> `/``` /`---` sequences can never
# become headings, list items, quotes, fences or rules.
_MD_LINE_BREAKS = str.maketrans(
    {
        "\r": " ",
        "\n": " ",
        "\u2028": " ",
        "\u2029": " ",
    }
)

_MD_ESCAPE = str.maketrans(
    {char: "\\" + char for char in _MD_ESCAPABLE}
)


def _md_leaf(value: object) -> str:
    """Owner leaf as literal inline Markdown text — every ASCII
    punctuation mark is escaped and embedded line separators collapse
    to spaces, so owner data can never introduce structural elements,
    links, autolinks or formatting instructions of its own."""
    return str(value).translate(_MD_ESCAPE).translate(_MD_LINE_BREAKS)

def _md_format_structured(
    node: object,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    """Markdown variant of ``_format_structured``: ``- **key:** value``
    bullets over the same traversal, control-plane filter and bounds."""
    if depth > 3:
        return []
    indent = "  " * depth
    if isinstance(node, Mapping):
        lines: list[str] = []
        for key, value in node.items():
            key = str(key)
            canon = _canonical_key(key)
            if canon in _CONTROL_PLANE_KEYS:
                continue
            display = (
                field_display_label(canon, key, field_labels)
                if field_labels is not None
                else key
            )
            if isinstance(value, Mapping):
                sub = _md_format_structured(
                    value, depth + 1, field_labels=field_labels
                )
                lines.append(f"{indent}- **{_md_leaf(display)}:**")
                lines.extend(sub or [f"{indent}  - {{}}"])
            elif isinstance(value, (list, tuple)):
                items = list(value)[:MAX_RENDER_LIST_ITEMS]
                if items:
                    lines.append(f"{indent}- **{_md_leaf(display)}:**")
                    lines.extend(
                        _md_format_list(
                            items, depth + 1, field_labels=field_labels
                        )
                    )
                else:
                    lines.append(
                        f"{indent}- **{_md_leaf(display)}:** (vazio)"
                    )
            else:
                if value is None:
                    continue
                lines.append(
                    f"{indent}- **{_md_leaf(display)}:** "
                    f"{_md_leaf(value)}"
                )
        return lines
    return []

def _md_format_list(
    items: list,
    depth: int,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    indent = "  " * depth
    lines: list[str] = []
    for item in items:
        if isinstance(item, Mapping):
            first = True
            for key, value in item.items():
                canon = _canonical_key(key)
                if canon in _CONTROL_PLANE_KEYS:
                    continue
                if (
                    isinstance(value, (Mapping, list, tuple))
                    or value is None
                ):
                    continue
                display = (
                    field_display_label(canon, key, field_labels)
                    if field_labels is not None
                    else key
                )
                if first:
                    lines.append(
                        f"{indent}- **{_md_leaf(display)}:** "
                        f"{_md_leaf(value)}"
                    )
                    first = False
                else:
                    lines.append(
                        f"{indent}  - **{_md_leaf(display)}:** "
                        f"{_md_leaf(value)}"
                    )
            if first:
                lines.append(f"{indent}- {{}}")
        elif isinstance(item, (list, tuple)):
            return []
        else:
            lines.append(f"{indent}- {_md_leaf(item)}")
    return lines

def _md_format_records(
    items: list,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> list[str]:
    """Bounded numbered record list — same selection/order as
    ``_format_records`` with Markdown list syntax."""
    indent = "  " * depth
    lines: list[str] = []
    for idx, item in enumerate(items, 1):
        if isinstance(item, Mapping):
            lines.append(f"{indent}{idx}.")
            sub = _md_format_structured(
                item, depth + 1, field_labels=field_labels
            )
            lines.extend(sub or [f"{indent}   - {{}}"])
        else:
            lines.append(f"{indent}{idx}. {_md_leaf(item)}")
    return lines

def _md_business_lines(
    node: Mapping,
    depth: int = 0,
    field_labels: FieldLabels | None = None,
) -> list[str] | None:
    """Markdown variant of ``_business_lines`` — identical envelope
    unwrapping and selection decisions; only the line syntax differs."""
    if depth > 2:
        return None
    for key in _RESOLVER_ENVELOPE_KEYS:
        payload = node.get(key)
        if isinstance(payload, Mapping):
            items = payload.get(_ITEMS_KEY)
            if isinstance(items, list):
                if not items:
                    return [EMPTY_RESULT_TEXT]
                if len(items) == 1 and isinstance(items[0], Mapping):
                    return (
                        _md_format_structured(
                            items[0], field_labels=field_labels
                        )
                        or None
                    )
                return _md_format_records(
                    items, field_labels=field_labels
                )
            nested = _md_business_lines(
                payload, depth + 1, field_labels=field_labels
            )
            if nested is not None:
                return nested
            return (
                _md_format_structured(payload, field_labels=field_labels)
                or None
            )
        if isinstance(payload, list):
            if not payload:
                return [EMPTY_RESULT_TEXT]
            return _md_format_records(payload, field_labels=field_labels)
    return None
