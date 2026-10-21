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
  language is emitted only when the proving field's own schema key
  declares modification semantics (E3-R2);
- no continuity offer is emitted while no serviceable mechanism
  backs it (E3-R3).

Returning ``None`` degrades to the existing synthesized render —
composition is an enhancement, never a correctness dependency.
"""

from __future__ import annotations

import re
import unicodedata
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

# E3-R2 — modification semantics are proven only by the proving
# field's OWN schema key (owner-declared business meaning), never by
# provider metadata prose or by the model. A normalized key qualifies
# only when it carries a modification marker and every remaining
# token is a generic connective — an extra qualifier (``original``,
# ``prevista``…) leaves the meaning unclassified, so the response
# degrades to neutral wording instead of guessing.
_MODIFICATION_FIELD_TOKENS = frozenset(
    {
        "alteracao",
        "alterado",
        "alterada",
        "atualizacao",
        "atualizado",
        "atualizada",
        "modificacao",
        "modificado",
        "modificada",
        "modification",
        "modified",
        "update",
        "updated",
        "revisao",
        "revisado",
        "revision",
        "revised",
        "changed",
    }
)
_TEMPORAL_FIELD_CONNECTIVES = frozenset(
    {
        "a",
        "da",
        "de",
        "do",
        "e",
        "em",
        "o",
        "data",
        "date",
        "dt",
        "first",
        "hora",
        "last",
        "mais",
        "primeira",
        "primeiro",
        "recente",
        "rec",
        "record",
        "reg",
        "registro",
        "time",
        "timestamp",
        "ts",
        "ultima",
        "ultimo",
    }
)
_FIELD_TOKEN_SPLIT = re.compile(r"[^0-9a-z]+")
_CAMEL_BOUNDARY = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")


def _field_tokens(field_name: str) -> tuple[str, ...]:
    """Split a field key into comparable tokens — snake/kebab/space
    and camelCase boundaries, accents folded, lower-cased."""

    spaced = _CAMEL_BOUNDARY.sub(" ", field_name)
    folded = unicodedata.normalize("NFKD", spaced)
    ascii_only = "".join(
        ch for ch in folded if not unicodedata.combining(ch)
    ).lower()
    return tuple(tok for tok in _FIELD_TOKEN_SPLIT.split(ascii_only) if tok)


def _field_declares_modification(field_name: str | None) -> bool:
    """True only when the proving field's own key declares
    modification — conservative: every token must be a marker or a
    generic connective, and at least one marker must be present."""

    if not isinstance(field_name, str) or not field_name.strip():
        return False
    tokens = _field_tokens(field_name)
    if not tokens:
        return False
    allowed = _MODIFICATION_FIELD_TOKENS | _TEMPORAL_FIELD_CONNECTIVES
    return any(tok in _MODIFICATION_FIELD_TOKENS for tok in tokens) and all(
        tok in allowed for tok in tokens
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
    ordering_field: str | None,
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
        # E3-R2: ordering proves ORDER only. The alteration claim is
        # allowed solely when the proving field's own schema key
        # declares modification semantics; otherwise the wording is
        # neutral and the clause states the meaning is unproven.
        modified = _field_declares_modification(ordering_field)
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

    # E3-R3: no continuity offer is emitted — the governed contracts
    # carry no serviceable mechanism (no expandable-detail block, no
    # proven next-turn retrieval binding), so promising detail would
    # offer a capability that cannot be served.

    return CriComposition(
        "\n\n".join(paragraphs), presented, tuple(limitations)
    )
