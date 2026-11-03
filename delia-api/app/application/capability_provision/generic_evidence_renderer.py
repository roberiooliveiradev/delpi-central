"""DELIA-C3-UNIFIED-EVIDENCE-PRESENTATION-01 generic evidence surface.

One deterministic, owner-agnostic Markdown projection for authorized
business evidence — flat or nested. The renderer never inspects
provider, capability or field names, never calls a model and never
executes anything: it formats sanitized owner data and reports
exactly what it could not present.

Contract (REWORK-01):

- **Fidelity** — every authorized leaf value and field identity is
  preserved verbatim (Markdown-escaped, never semantically altered);
  there is no convenience truncation of strings or labels.
- **No silent loss** — the only bounds are legitimate resource
  controls (node budget, recursion depth). Any node, field or
  descendant left out by those controls marks the render partial and
  is counted — never a quiet drop.
- **Owner pagination is not a render concern** — ``has_more`` /
  totals / coverage belong to the owning API contract and are
  reported by the composition layer, separate from the technical
  ``OMISSION_*`` reasons below.
- **Governed labels** — field names resolve through the single
  governed label contract (``field_display_label``): governed
  vocabulary label when declared, otherwise the raw owner key
  humanized without translation; digit-bearing keys stay byte-exact.
- **Safety** — every emitted leaf is escaped against the full
  CommonMark-escapable ASCII set (same proof as ``_md_leaf``), so
  untrusted owner text can never form emphasis, links, autolinks,
  code spans, headings, list items or inline HTML. Embedded line
  separators become indented continuation lines — content is
  preserved and each continuation stays structural-safe.
"""
from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

from app.application.capability_provision.outcome_assessment import (
    _canonical_key,
)

PRESENTATION_COMPLETE = "complete"
PRESENTATION_PARTIAL_OWNER_PAGINATION = "partial_owner_pagination"
PRESENTATION_PARTIAL_PRESENTATION_LIMIT = "partial_presentation_limit"
PRESENTATION_INCOMPLETE_SOURCE = "incomplete_source"
PRESENTATION_UNKNOWN_COMPLETENESS = "unknown_completeness"

# Technical omission reasons — distinct from owner-side pagination:
# the render itself could not show every received node because a
# legitimate resource bound was reached.
OMISSION_NODE_BUDGET = "node_budget"
OMISSION_MAX_DEPTH = "max_depth"

# Legitimate resource controls (never correctness gates): the node
# budget bounds transport/render size for hostile or pathological
# payloads; the depth bound prevents unbounded recursion. Both are
# reported — never silent.
_PRESENTATION_NODE_BUDGET = 512
_PRESENTATION_MAX_DEPTH = 6

# Full CommonMark-escapable ASCII punctuation — identical proof to the
# ``_md_leaf`` contract: escaped punctuation renders identically, so
# business values display verbatim while being unable to form any
# structural Markdown element.
_MD_ESCAPABLE = "!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
_MD_ESCAPE = str.maketrans({char: "\\" + char for char in _MD_ESCAPABLE})

# CR/LF and the Unicode line/paragraph separators inside owner data —
# each embedded line is preserved as an indented continuation line
# (escaped), so multi-line values stay literal but can never inject
# headings, list items, fences or rules.
_LINE_BREAKS = re.compile(r"\r\n|\r|\n| | ")

_DEEP_OMISSION_MARKER = "(estrutura profunda omitida)"


def _md_escape(text: str) -> str:
    return str(text).translate(_MD_ESCAPE)


# ------------------------------------------------------------------
# Governed field-label resolution (canonical home — moved from
# conversational_response.py, which re-exports these names so the
# resolver stays single-source across CRI, detail and comparison
# paths).
#
# A key absent from the governed map is *unknown*: the owner wording
# is preserved verbatim — words humanize (underscores become
# spaces), digit-bearing code-shaped keys stay byte-exact. A field
# name is never translated nor merged (``codigo_processo`` must
# never render as ``Codigoprocesso`` or an invented meaning), and a
# label is never truncated — field identity must stay recoverable.
# ------------------------------------------------------------------

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


def _render_label(key: object, field_labels: FieldLabels | None) -> str:
    """Untruncated Markdown-safe label for one field key: governed
    label when declared, else the owner key humanized verbatim —
    escaped so a hostile key can never form structure."""
    return _md_escape(
        field_display_label(_canonical_key(str(key)), key, field_labels)
    )


def _value_lines(value: object) -> list[str]:
    """One owner leaf as escaped lines — verbatim, never truncated.

    Multi-line text splits into one entry per embedded line; the
    caller emits the first inline and the rest as indented
    continuations, so the value stays literal without ever opening a
    new structural element.
    """
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["sim" if value else "nao"]
    if isinstance(value, (int, float)):
        return [_md_escape(str(value))]
    parts = _LINE_BREAKS.split(str(value))
    return [_md_escape(part) for part in parts]


@dataclass(frozen=True, slots=True)
class EvidenceRender:
    """Structured result of one evidence render.

    ``presented_items`` counts the top-level collection elements
    actually emitted (for a records list: the records presented);
    ``total_items`` is the distinct input count at that level.
    ``omitted_nodes`` counts every field/item/descendant the resource
    bounds left out — ``partial`` is true whenever any omission
    happened, so callers can always distinguish a complete render
    from a technically bounded one.
    """

    lines: tuple[str, ...]
    presented_items: int
    total_items: int
    rendered_nodes: int
    omitted_nodes: int
    omission_reasons: tuple[str, ...]

    @property
    def partial(self) -> bool:
        return bool(self.omission_reasons)


class _Budget:
    """Mutable render accounting shared by the recursion."""

    __slots__ = ("remaining", "rendered", "omitted", "reasons")

    def __init__(self, nodes: int) -> None:
        self.remaining = nodes
        self.rendered = 0
        self.omitted = 0
        self.reasons: list[str] = []

    def consume(self) -> bool:
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        self.rendered += 1
        return True

    def omit(self, count: int, reason: str) -> None:
        self.omitted += count
        if reason not in self.reasons:
            self.reasons.append(reason)


def _render_node(
    value: object,
    depth: int,
    field_labels: FieldLabels | None,
    budget: _Budget,
    out: list[str],
    *,
    count_items: bool = False,
) -> int:
    """Recursive render — returns top-level items emitted when
    ``count_items`` (the record-collection level), else ``0``.

    Every visited sibling consumes one budget node; when the budget
    or the depth bound cuts a branch short, every skipped sibling is
    counted as omitted with its reason — nothing is dropped without
    accounting.
    """
    indent = "  " * depth
    presented = 0
    if isinstance(value, Mapping):
        members = list(value.items())
        for index, (key, child) in enumerate(members):
            if not budget.consume():
                budget.omit(
                    len(members) - index, OMISSION_NODE_BUDGET
                )
                break
            label = _render_label(key, field_labels)
            if isinstance(child, (Mapping, list, tuple)):
                if not child:
                    out.append(f"{indent}- {label}: {{}}")
                elif depth + 1 >= _PRESENTATION_MAX_DEPTH:
                    out.append(
                        f"{indent}- {label}: {_DEEP_OMISSION_MARKER}"
                    )
                    budget.omit(1, OMISSION_MAX_DEPTH)
                else:
                    out.append(f"{indent}- {label}:")
                    _render_node(
                        child, depth + 1, field_labels, budget, out
                    )
            else:
                lines = _value_lines(child)
                out.append(f"{indent}- {label}: {lines[0]}")
                for continuation in lines[1:]:
                    out.append(f"{indent}  {continuation}")
    elif isinstance(value, (list, tuple)):
        items = list(value)
        for index, item in enumerate(items):
            if not budget.consume():
                budget.omit(len(items) - index, OMISSION_NODE_BUDGET)
                break
            if count_items:
                presented += 1
            if isinstance(item, (Mapping, list, tuple)):
                if not item:
                    out.append(f"{indent}- {{}}")
                elif depth + 1 >= _PRESENTATION_MAX_DEPTH:
                    out.append(f"{indent}- {_DEEP_OMISSION_MARKER}")
                    budget.omit(1, OMISSION_MAX_DEPTH)
                else:
                    sub: list[str] = []
                    _render_node(
                        item, depth + 1, field_labels, budget, sub
                    )
                    if sub:
                        out.append(f"{indent}-")
                        out.extend(sub)
                    else:
                        out.append(f"{indent}- {{}}")
            else:
                lines = _value_lines(item)
                out.append(f"{indent}- {lines[0]}")
                for continuation in lines[1:]:
                    out.append(f"{indent}  {continuation}")
    else:
        lines = _value_lines(value)
        out.append(f"{indent}- {lines[0]}")
        for continuation in lines[1:]:
            out.append(f"{indent}  {continuation}")
    return presented


def render_business_evidence(
    value: object,
    field_labels: FieldLabels | None = None,
) -> EvidenceRender:
    """Render authorized evidence into generic Markdown lines.

    Accepts any JSON-shaped value — records, objects, arrays,
    hierarchies, mixed structures — with no per-owner or
    per-capability branch. Returns an ``EvidenceRender`` whose
    ``partial`` flag and omission accounting distinguish a complete
    render from a technically bounded one; caller-side owner
    pagination is a separate axis reported elsewhere.
    """
    budget = _Budget(_PRESENTATION_NODE_BUDGET)
    out: list[str] = []
    if isinstance(value, (list, tuple)):
        # Every authorized occurrence renders — order and positions
        # preserved. Identical payloads may be legitimate business
        # occurrences; deduplication belongs to the owner's contract,
        # never to a generic presentation surface.
        items = list(value)
        presented = _render_node(
            items, 0, field_labels, budget, out, count_items=True
        )
        total = len(items)
    else:
        _render_node(value, 0, field_labels, budget, out)
        presented = 1 if out else 0
        total = 1
    return EvidenceRender(
        lines=tuple(out),
        presented_items=presented,
        total_items=total,
        rendered_nodes=budget.rendered,
        omitted_nodes=budget.omitted,
        omission_reasons=tuple(budget.reasons),
    )
