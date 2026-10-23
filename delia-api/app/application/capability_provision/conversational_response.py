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

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from app.application.capability_provision.outcome_assessment import (
    OUTCOME_ANSWERED,
    OUTCOME_CONTRACT_FACTS,
    OUTCOME_EMPTY_RESULT,
    OUTCOME_ENVELOPE_ONLY,
    OUTCOME_INSUFFICIENT,
    AnswerRequirements,
    OutcomeVerdict,
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
