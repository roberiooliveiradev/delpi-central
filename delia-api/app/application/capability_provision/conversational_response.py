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

from app.application.capability_provision.generic_evidence_renderer import (
    MAX_RENDER_LIST_ITEMS,
    parse_temporal_value,
    _CONTROL_PLANE_KEYS,
    _IDENTITY_FIRST_KEYS,
    _RESOLVER_ENVELOPE_KEYS,
    _UUID_VALUE_RE,
    _canonical_key,
    _record_identifier,
    _sanitize_renderable,
    _sanitize_renderable_counted,
)
from app.application.interaction.contracts import (
    LIMITATION_EVIDENCE_PROJECTION_PARTIAL,
    LIMITATION_INSUFFICIENT_EVIDENCE,
    LIMITATION_RESULT_TRUNCATED,
)
from app.application.capability_provision.generic_evidence_renderer import (
    FieldLabels,
    field_clause_label,
    field_display_label,
    field_label_parts,
    render_business_evidence,
    unmapped_field_label,
)

# Owner-published contract rows are capability-surface metadata —
# bounded in count and per-row size so a large catalog can never
# flood the response.
MAX_CONTRACT_FACT_ROWS = 8
_MAX_CONTRACT_FACT_CHARS = 300

# Reason -> insufficiency vocabulary key, in proximate-cause order:
# the reason closest to what the user actually asked leads the
# honest explanation.


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


# ------------------------------------------------------------------
# Field-label resolution (C3-S3 / RQ-SA05 / D8)
#
# Canonical home: ``generic_evidence_renderer.py`` — the unified
# evidence surface owns the single governed projection for owner
# field names. This module re-exports the resolver so every consumer
# (detail lines, focused-answer clauses, CRI anchors, comparisons
# and the orchestration glue) resolves through one source and the
# paths can never diverge.

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




# ------------------------------------------------------------------
# M06/R4 — deterministic presentation helpers relocated from the
# orchestration coordinator (plan 125): pure format/projection
# ownership — no capability execution, no provider access, no
# authorization decisions. Behavior is byte-parity, not rewritten.
# ------------------------------------------------------------------

MAX_RENDER_CONTENT_CHARS = 2000




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
        # Presentation ordering only — business-identity fields lead,
        # technical metadata follows; every owner field still renders.
        ordered = sorted(
            node.items(),
            key=lambda kv: 0
            if _canonical_key(kv[0]) in _IDENTITY_FIRST_KEYS
            else 1,
        )
        for key, value in ordered:
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
            for key, value in sorted(
                item.items(),
                key=lambda kv: 0
                if _canonical_key(kv[0]) in _IDENTITY_FIRST_KEYS
                else 1,
            ):
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

_SUBJECT_CONTEXT_KEYS = ("root", "parent", "subject")


def _structural_subject(payload: Mapping) -> Mapping | None:
    """First owner-declared subject object in a data envelope."""
    for key in _SUBJECT_CONTEXT_KEYS:
        candidate = payload.get(key)
        if isinstance(candidate, Mapping) and candidate:
            return candidate
    return None


def _project_subject_with_items(
    payload: Mapping,
    items: list,
    *,
    field_labels: FieldLabels | None,
    format_structured,
    format_records,
) -> list[str] | None:
    """Keep subject identity when an envelope also publishes items.

    A single-item list must not replace an authoritative root/parent/
    subject already declared on the same payload — that erases the
    user's identifier and turns a BOM child into a false primary.
    """
    subject = _structural_subject(payload)
    if subject is None:
        return None
    lines = format_structured(subject, field_labels=field_labels) or []
    if items:
        child_lines = format_records(items, field_labels=field_labels)
        if child_lines:
            lines.append("Componentes:")
            lines.extend(child_lines)
    else:
        lines.append("Componentes: (vazio)")
    completeness = payload.get("is_complete")
    if isinstance(completeness, bool):
        lines.append(f"is_complete: {str(completeness).lower()}")
    return lines or None


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
                with_subject = _project_subject_with_items(
                    payload,
                    items,
                    field_labels=field_labels,
                    format_structured=_format_structured,
                    format_records=_format_records,
                )
                if with_subject is not None:
                    return with_subject
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
            for key, value in sorted(
                item.items(),
                key=lambda kv: 0
                if _canonical_key(kv[0]) in _IDENTITY_FIRST_KEYS
                else 1,
            ):
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
                with_subject = _project_subject_with_items(
                    payload,
                    items,
                    field_labels=field_labels,
                    format_structured=_md_format_structured,
                    format_records=_md_format_records,
                )
                if with_subject is not None:
                    return with_subject
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
