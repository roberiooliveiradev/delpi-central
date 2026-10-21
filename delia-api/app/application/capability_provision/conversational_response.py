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
  ``insufficient_evidence`` instead of claiming success.

Returning ``None`` degrades to the existing synthesized render —
composition is an enhancement, never a correctness dependency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from app.application.capability_provision.outcome_assessment import (
    OUTCOME_ANSWERED,
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
    vocabulary: Mapping[str, Mapping[str, str]],
) -> CriComposition | None:
    """Compose the governed conversational response, or ``None``.

    All texts come from the validated declarative vocabulary — this
    function selects *which* template applies by verdict shape and
    substitutes only evidence-derived placeholders.
    """

    leads = vocabulary.get("leads") or {}
    temporal = vocabulary.get("temporal_clauses") or {}
    insufficiency = vocabulary.get("insufficiency") or {}
    continuity = vocabulary.get("continuity") or {}
    labels = vocabulary.get("labels") or {}
    req = requirements or AnswerRequirements()
    params = {
        "identifier": "",
        "date": ordering_date or "",
        "count": "",
        "presented": "",
        "returned": len(records),
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
        text = _format(insufficiency.get(key), **params)
        return (
            CriComposition(text, 0)
            if text is not None
            else None
        )

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
        lead_key = (
            "ordering_newest_single"
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
                    temporal.get(ordering), **params
                )
                if clause is None:
                    return None
                paragraphs.append(clause)
            presented = 1
            # The extreme record's unshown fields justify a detail
            # offer — identifier/title are already in the lead.
            if len(records[0].fields) > 2:
                offer = _format(continuity.get("detail_offer"), **params)
                if offer is not None:
                    paragraphs.append(offer)
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
    if presented < len(records):
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

    # ---- continuity: offer detail only when it is real -------------
    has_unshown_fields = any(
        len(record.fields) > MAX_FIELDS_PER_RECORD
        for record in records[: max(presented, 1)]
    )
    if has_unshown_fields:
        offer = _format(continuity.get("detail_offer"), **params)
        if offer is not None:
            paragraphs.append(offer)

    return CriComposition(
        "\n\n".join(paragraphs), presented, tuple(limitations)
    )
