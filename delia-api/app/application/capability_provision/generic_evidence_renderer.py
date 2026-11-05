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
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from app.domain.specialist_interop.model import SpecialistOutcome


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


# ============================================================
# Deterministic owner-payload projection contract (doc 244/245/256)
# Consolidated from the retired outcome_assessment and
# paginated_result_semantics modules: envelope/count proofs,
# control-plane stripping, sanitization/redaction, entity-schema
# projection, comparison/ordering facts — all bounded and
# provider-neutral, never model inference. Semantic verdicts and
# regex intent classifiers were removed, not relocated.
# ============================================================
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
        # Owner-published discovery-candidate vocabulary
        # (discover_delpi_information catalog descriptors — never
        # business records; DELIA-C3-EVIDENCE-TO-ANSWER-...-01).
        "candidatetoken",
        "argumentschema",
        "semantichints",
        "retrievalscore",
        "paginationhints",
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
    if len(weak) >= 2 or len(strong) >= 2:
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


def _sanitize_renderable_counted(node: object) -> tuple[object, int]:
    """Sanitize AND count list elements dropped by the bound.

    Security contract is identical to ``_sanitize_renderable`` —
    sensitive keys redact, hostile text redacts, lists stay bounded by
    ``MAX_RENDER_LIST_ITEMS`` (a legitimate resource control). The
    difference: the returned count reports every authorized item the
    bound left out, so callers must propagate partiality instead of
    mistaking the bounded collection for the complete one.
    """
    omitted = [0]

    def rec(n: object) -> object:
        if isinstance(n, Mapping):
            return {
                str(k): (
                    REDACTION_MARKER
                    if _is_sensitive_key(k)
                    else rec(v)
                )
                for k, v in n.items()
            }
        if isinstance(n, (list, tuple)):
            items = list(n)
            if len(items) > MAX_RENDER_LIST_ITEMS:
                omitted[0] += len(items) - MAX_RENDER_LIST_ITEMS
            return [rec(v) for v in items[:MAX_RENDER_LIST_ITEMS]]
        if isinstance(n, str):
            return _redact_text(n)
        return n

    return rec(node), omitted[0]


def _sanitize_renderable(node: object) -> object:
    """Redact sensitive credential material from rendered structure.

    Remote structured payloads are untrusted data: sensitive keys
    (canonical normalized match) have their values replaced with the
    redaction marker — the key stays so shape is preserved and no
    secret value, length, prefix or hash is exposed. Recurses into
    mappings and bounded lists; candidate_token is covered by the
    canonical set. List items beyond ``MAX_RENDER_LIST_ITEMS`` stay
    bounded — callers that present collections must use
    ``_sanitize_renderable_counted`` so the drop is never silent.
    """
    sanitized, _ = _sanitize_renderable_counted(node)
    return sanitized


_GENERIC_COMPLETION_TEXTS = frozenset(
    {"execution completed.", "discovery completed.", "ok", "success"}
)


def _is_generic_status(text: str) -> bool:
    return text.strip().lower() in _GENERIC_COMPLETION_TEXTS


# ------------------------------------------------------------------
# Outcome projection + verdict application (R3/M04, plan 125). The
# typed EvidenceFacts projection and the verdict->limitation rule
# moved from orchestration.py: the assessment owner now produces the
# facts it classifies AND applies the bounded insufficiency marking.
# Record extraction stays injectable because the synthesis resolver
# depends on guidance machinery still owned by the coordinator
# (later milestones).
# ------------------------------------------------------------------


_RESULT_CONTEXT_LABEL_KEYS = frozenset({"entity", "shape"})
_RESULT_CONTEXT_SUBJECT_KEYS = ("root", "parent", "subject")
_RESULT_CONTEXT_INNER_KEYS = ("data", "result", "payload", "response")
_RESULT_CONTEXT_LABEL_MAX_CHARS = 64
_RESULT_CONTEXT_SUBJECT_MAX_FIELDS = 12
_RESULT_CONTEXT_SUBJECT_STR_MAX_CHARS = 80




class CountResolutionKind(str, Enum):
    AUTHORITATIVE_TOTAL = "AUTHORITATIVE_TOTAL"
    COMPLETE_AGGREGATE = "COMPLETE_AGGREGATE"
    PARTIAL_UNKNOWN = "PARTIAL_UNKNOWN"
    EMPTY = "EMPTY"
    PAGE_SLICE_NOT_TOTAL = "PAGE_SLICE_NOT_TOTAL"


# Default operational bound for governed page walks (R5).
DEFAULT_MAX_PAGES = 20

_TOTAL_KEYS = ("total_count", "total", "totalcount", "count_total")
_ID_KEYS = ("id", "ticket_id", "ticketid")


@dataclass(frozen=True, slots=True)
class PaginationEnvelope:
    items: tuple[Mapping[str, Any], ...]
    page: int | None
    page_size: int | None
    has_more: bool | None
    total_count: int | None

    @property
    def returned_count(self) -> int:
        return len(self.items)


@dataclass(frozen=True, slots=True)
class PageAggregationResult:
    items: tuple[Mapping[str, Any], ...]
    pages_fetched: int
    complete: bool
    duplicate_ids: tuple[str, ...]
    failed: bool
    failure_reason: str | None
    authoritative_total: int | None

    @property
    def unique_count(self) -> int:
        return len(self.items)


@dataclass(frozen=True, slots=True)
class CountResolution:
    kind: CountResolutionKind
    total: int | None
    returned_on_page: int
    has_more: bool | None
    message: str


UNKNOWN_TOTAL_MESSAGE = (
    "Consultei uma parte dos chamados, mas não tenho evidência "
    "suficiente para confirmar o total."
)

PAGE_SLICE_LIST_HEADER = (
    "Mostrando {count} registro(s) nesta página; há mais resultados "
    "além desta página — este número não é o total."
)

COMPLETE_COUNT_MESSAGE = "Total confirmado nesta consulta: {total}."

AUTHORITATIVE_COUNT_MESSAGE = (
    "Total informado pela fonte nesta consulta: {total}."
)

EMPTY_COUNT_MESSAGE = "Nenhum chamado encontrado nesta consulta."

VISIBLE_NOT_PERSONAL_NOTE = (
    " Este total refere-se aos chamados retornados pela consulta "
    "autorizada, não a um escopo pessoal de responsável ou solicitante "
    "sem filtro comprovado."
)

def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return None


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _read_total(node: Mapping[str, Any]) -> int | None:
    for key in _TOTAL_KEYS:
        if key in node:
            total = _as_int(node.get(key))
            if total is not None and total >= 0:
                return total
    return None


def extract_pagination_envelope(
    structured: object,
) -> PaginationEnvelope | None:
    """Detect owner list pages: items + pagination metadata.

    Recognizes top-level or single-envelope payloads. Returns None when
    the shape is not a paginated item list.
    """
    if not isinstance(structured, Mapping):
        return None
    candidates: list[Mapping[str, Any]] = [structured]
    for key in ("data", "result", "payload", "response"):
        inner = structured.get(key)
        if isinstance(inner, Mapping):
            candidates.append(inner)
    for node in candidates:
        items = node.get("items")
        if not isinstance(items, list):
            continue
        has_page_meta = any(
            k in node for k in ("page", "page_size", "has_more", *_TOTAL_KEYS)
        )
        if not has_page_meta and not items:
            # Empty non-paginated items list is not a count envelope.
            continue
        if not has_page_meta and items:
            # Bare items without pagination metadata — still usable as a
            # complete page only when the caller treats has_more as None.
            pass
        normalized_items = tuple(
            item for item in items if isinstance(item, Mapping)
        )
        return PaginationEnvelope(
            items=normalized_items,
            page=_as_int(node.get("page")),
            page_size=_as_int(node.get("page_size")),
            has_more=_as_bool(node.get("has_more")),
            total_count=_read_total(node),
        )
    return None


def item_stable_id(item: Mapping[str, Any]) -> str | None:
    for key in _ID_KEYS:
        if key in item and item[key] is not None:
            text = str(item[key]).strip()
            if text:
                return text
    return None


def _is_first_page(page: int | None) -> bool:
    """True when the envelope is the first page of a query.

    Missing ``page`` is treated as first-page only when the owner also
    signals explicit completion (``has_more=False``) — never when
    completeness is unsigned.
    """
    return page is None or page <= 1

def aggregate_paginated_pages(
    pages: Sequence[Mapping[str, Any] | PaginationEnvelope | None],
    *,
    max_pages: int = DEFAULT_MAX_PAGES,
) -> PageAggregationResult:
    """Merge ordered owner pages with integrity checks.

    ``complete`` requires explicit evidence of a finished walk:

    - authoritative owner total, or
    - walk that starts at the first page, contiguous page numbers (when
      present), last page ``has_more is False``, no duplicate ids, no
      page failures, and no missing stable ids when counting.

    ``has_more is None`` never proves completion. An isolated last page
    (``page>1``) never proves the full query total.
    """
    merged: list[Mapping[str, Any]] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    pages_fetched = 0
    authoritative: int | None = None
    last_has_more: bool | None = None
    started_at_first = False
    expected_page: int | None = None
    seen_page_numbers: set[int] = set()
    missing_stable_ids = 0
    failure_reason: str | None = None

    bounded = list(pages)[: max(0, max_pages)]
    for raw in bounded:
        if raw is None:
            return PageAggregationResult(
                items=tuple(merged),
                pages_fetched=pages_fetched,
                complete=False,
                duplicate_ids=tuple(duplicates),
                failed=True,
                failure_reason="page_failure",
                authoritative_total=authoritative,
            )
        envelope = (
            raw
            if isinstance(raw, PaginationEnvelope)
            else extract_pagination_envelope(raw)
        )
        if envelope is None:
            return PageAggregationResult(
                items=tuple(merged),
                pages_fetched=pages_fetched,
                complete=False,
                duplicate_ids=tuple(duplicates),
                failed=True,
                failure_reason="malformed_page",
                authoritative_total=authoritative,
            )

        page_num = envelope.page
        if pages_fetched == 0:
            started_at_first = _is_first_page(page_num)
            if page_num is not None:
                expected_page = page_num
        if page_num is not None:
            if page_num in seen_page_numbers:
                failure_reason = "duplicate_page"
            elif expected_page is not None and page_num != expected_page:
                failure_reason = (
                    "out_of_order"
                    if page_num < expected_page
                    else "missing_intermediate_page"
                )
            seen_page_numbers.add(page_num)
            expected_page = page_num + 1

        if failure_reason is not None:
            return PageAggregationResult(
                items=tuple(merged),
                pages_fetched=pages_fetched,
                complete=False,
                duplicate_ids=tuple(duplicates),
                failed=True,
                failure_reason=failure_reason,
                authoritative_total=authoritative,
            )

        pages_fetched += 1
        if envelope.total_count is not None:
            if (
                authoritative is not None
                and envelope.total_count != authoritative
            ):
                return PageAggregationResult(
                    items=tuple(merged),
                    pages_fetched=pages_fetched,
                    complete=False,
                    duplicate_ids=tuple(duplicates),
                    failed=True,
                    failure_reason="authoritative_total_conflict",
                    authoritative_total=authoritative,
                )
            authoritative = envelope.total_count
        last_has_more = envelope.has_more
        for item in envelope.items:
            item_id = item_stable_id(item)
            if item_id is None:
                missing_stable_ids += 1
                merged.append(item)
                continue
            if item_id in seen:
                duplicates.append(item_id)
                continue
            seen.add(item_id)
            merged.append(item)
        if envelope.has_more is False:
            break

    if missing_stable_ids and authoritative is None:
        # Without stable ids we cannot prove uniqueness → never exact.
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=False,
            duplicate_ids=tuple(duplicates),
            failed=False,
            failure_reason="missing_stable_ids",
            authoritative_total=authoritative,
        )

    if duplicates:
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=False,
            duplicate_ids=tuple(duplicates),
            failed=False,
            failure_reason="duplicate_ticket_ids",
            authoritative_total=authoritative,
        )

    if authoritative is not None:
        # Owner total is authoritative even mid-walk; uniqueness still
        # required above. Do not recompute from page lengths.
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=True,
            duplicate_ids=(),
            failed=False,
            failure_reason=None,
            authoritative_total=authoritative,
        )

    # Explicit last-page signal only closes a walk that started at page 1.
    if (
        last_has_more is False
        and started_at_first
        and pages_fetched > 0
    ):
        return PageAggregationResult(
            items=tuple(merged),
            pages_fetched=pages_fetched,
            complete=True,
            duplicate_ids=(),
            failed=False,
            failure_reason=None,
            authoritative_total=None,
        )

    reason = "partial_unknown"
    if last_has_more is None:
        reason = "unsigned_completeness"
    elif not started_at_first:
        reason = "not_started_at_first_page"
    elif pages_fetched >= max_pages and last_has_more is True:
        reason = "max_pages_exceeded"
    elif last_has_more is True:
        reason = "has_more_remaining"

    return PageAggregationResult(
        items=tuple(merged),
        pages_fetched=pages_fetched,
        complete=False,
        duplicate_ids=(),
        failed=False,
        failure_reason=reason,
        authoritative_total=None,
    )


def resolve_count_semantics(
    envelope: PaginationEnvelope | None,
    *,
    aggregation: PageAggregationResult | None = None,
) -> CountResolution:
    """Map owner page / aggregation evidence to count wording."""
    if aggregation is not None:
        if aggregation.failed:
            return CountResolution(
                kind=CountResolutionKind.PARTIAL_UNKNOWN,
                total=None,
                returned_on_page=aggregation.unique_count,
                has_more=True,
                message=UNKNOWN_TOTAL_MESSAGE,
            )
        if aggregation.authoritative_total is not None:
            return CountResolution(
                kind=CountResolutionKind.AUTHORITATIVE_TOTAL,
                total=aggregation.authoritative_total,
                returned_on_page=aggregation.unique_count,
                has_more=False,
                message=AUTHORITATIVE_COUNT_MESSAGE.format(
                    total=aggregation.authoritative_total
                ),
            )
        if aggregation.complete and not aggregation.duplicate_ids:
            total = aggregation.unique_count
            if total == 0:
                return CountResolution(
                    kind=CountResolutionKind.EMPTY,
                    total=0,
                    returned_on_page=0,
                    has_more=False,
                    message=EMPTY_COUNT_MESSAGE,
                )
            return CountResolution(
                kind=CountResolutionKind.COMPLETE_AGGREGATE,
                total=total,
                returned_on_page=total,
                has_more=False,
                message=COMPLETE_COUNT_MESSAGE.format(total=total),
            )
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=aggregation.unique_count,
            has_more=True,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    if envelope is None:
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=0,
            has_more=None,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    if envelope.total_count is not None:
        return CountResolution(
            kind=CountResolutionKind.AUTHORITATIVE_TOTAL,
            total=envelope.total_count,
            returned_on_page=envelope.returned_count,
            has_more=envelope.has_more,
            message=AUTHORITATIVE_COUNT_MESSAGE.format(
                total=envelope.total_count
            ),
        )

    if envelope.returned_count == 0 and envelope.has_more is not True:
        # Empty last page with page>1 does not prove a zero global total.
        if envelope.has_more is False and not _is_first_page(envelope.page):
            return CountResolution(
                kind=CountResolutionKind.PARTIAL_UNKNOWN,
                total=None,
                returned_on_page=0,
                has_more=False,
                message=UNKNOWN_TOTAL_MESSAGE,
            )
        if envelope.has_more is None:
            return CountResolution(
                kind=CountResolutionKind.PAGE_SLICE_NOT_TOTAL,
                total=None,
                returned_on_page=0,
                has_more=None,
                message=UNKNOWN_TOTAL_MESSAGE,
            )
        return CountResolution(
            kind=CountResolutionKind.EMPTY,
            total=0,
            returned_on_page=0,
            has_more=envelope.has_more,
            message=EMPTY_COUNT_MESSAGE,
        )

    if envelope.has_more is True:
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=envelope.returned_count,
            has_more=True,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    if envelope.has_more is False:
        # A last page in isolation (page>1) is not the query total.
        if _is_first_page(envelope.page):
            total = envelope.returned_count
            return CountResolution(
                kind=CountResolutionKind.COMPLETE_AGGREGATE,
                total=total,
                returned_on_page=total,
                has_more=False,
                message=COMPLETE_COUNT_MESSAGE.format(total=total),
            )
        return CountResolution(
            kind=CountResolutionKind.PARTIAL_UNKNOWN,
            total=None,
            returned_on_page=envelope.returned_count,
            has_more=False,
            message=UNKNOWN_TOTAL_MESSAGE,
        )

    # No has_more signal — page length is not a proven total.
    return CountResolution(
        kind=CountResolutionKind.PAGE_SLICE_NOT_TOTAL,
        total=None,
        returned_on_page=envelope.returned_count,
        has_more=None,
        message=UNKNOWN_TOTAL_MESSAGE,
    )





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
    if text.isdigit():
        # Bare digit sequences are identifier-shaped (product codes,
        # document numbers, counters); fromisoformat would misread a
        # compact YYYYMMDD as a real date and corrupt the owner value.
        return None
    candidate = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(candidate)
    except ValueError:
        return None
    return parsed


def parse_temporal_value(value: object) -> datetime | None:
    """Public bounded temporal parse — same semantics as the
    projection's internal helper; strings only, never coerced."""

    return _parse_temporal(value)
