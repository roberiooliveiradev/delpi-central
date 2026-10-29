"""Governed CRI instruction resource — composition wiring.

CRI E2-R3 (doc 77): the response-intelligence answer-requirements
clause is a governed declarative artifact — versioned JSON reviewed
like code, never a second copy inside Python. Composition loads and
validates it once; a missing or invalid resource fails closed, so the
CRI enhancement never activates partially.

The resource is *instruction text only*: it declares no authority,
no domain rule and no execution permission — the model's proposal
remains a hypothesis the runtime verifies.
"""

from __future__ import annotations

import hashlib
import json
import re
import string
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

_RESOURCE_KIND = "instruction_clause"
_CLAUSE_VERSIONS = frozenset({"1", "2"})
_RESOURCE_KEYS = frozenset(
    {"resource_id", "version", "kind", "owner", "instruction_text"}
)
_REQUIRED_KEYS = _RESOURCE_KEYS
_MAX_INSTRUCTION_TEXT_BYTES = 4096

# CRI E3: presentation vocabulary resource — the response composer is
# a different consumer than the instruction clause, so it has its own
# kind/id/contract, never a second registry.
_VOCABULARY_RESOURCE_ID = "delia.cri.presentation_vocabulary"
_VOCABULARY_KIND = "presentation_vocabulary"
# E3-R1–R3 rework: v2 corrects count-source claims, splits temporal
# clauses by owner-declared field semantics and drops the
# unserviceable continuity offer. v1 is intentionally rejected.
# C3 contextual discovery: v3 adds the optional ``contract_facts``
# lead for owner-published capability-surface answers; v2 remains
# valid — the composition degrades to fallback when the entry is
# absent, never partially.
# C3-S3 (D8): v4 adds the optional ``field_labels`` section — a
# governed map of canonical field key → (article, label, suffix)
# shared by every presentation path; absent it stays an empty map,
# never partially loaded.
# Semantic relevance (plan 125 adendum): v5 adds the
# ``goal_mismatch``/``relevance_unproven`` insufficiency entries —
# honest degradation wording when returned evidence does not answer
# the stated goal or pertinence cannot be proven.
_VOCABULARY_VERSIONS = frozenset({"2", "3", "4", "5"})
_VOCABULARY_SECTIONS = (
    "leads",
    "temporal_clauses",
    "insufficiency",
    "labels",
)
_VOCABULARY_KEYS = frozenset(
    {
        "resource_id",
        "version",
        "kind",
        "owner",
        "field_labels",
        *_VOCABULARY_SECTIONS,
    }
)
_VOCABULARY_REQUIRED_ENTRIES: Mapping[str, frozenset[str]] = {
    "leads": frozenset(
        {
            "ordering_newest_single_modified",
            "ordering_newest_single_neutral",
            "ordering_oldest_single",
            "examples_fulfilled",
            "records_found",
            "single_found",
        }
    ),
    "temporal_clauses": frozenset(
        {
            "newest_first_modified",
            "newest_first_neutral",
            "oldest_first_modified",
            "oldest_first_neutral",
        }
    ),
    "insufficiency": frozenset(
        {
            "coverage_unproven",
            "ordering_unproven",
            "quantity_unproven",
            "fewer_than_requested_source",
            "fewer_than_requested_coverage",
            "fewer_than_requested_returned",
            "envelope_only",
            "empty_result",
            "partial_outcome",
            "generic",
        }
    ),
    "labels": frozenset(
        {"truncation_notice", "available_notice", "more_available"}
    ),
}
_VOCABULARY_PLACEHOLDERS = frozenset(
    {
        "identifier",
        "date",
        "count",
        "presented",
        "returned",
        "available",
        "requested",
        "delivered",
        "total",
    }
)
_MAX_VOCABULARY_SECTION_ENTRIES = 32
_MAX_VOCABULARY_ENTRY_BYTES = 512

# ``field_labels`` is a closed presentation map, not prose: canonical
# field keys (lowercase alnum) → declared (article, label, suffix)
# parts. Validation is structural — no placeholders, no model text.
_FIELD_LABEL_PARTS = frozenset({"article", "label", "suffix"})
_FIELD_LABEL_ARTICLES = frozenset({"o", "a"})
_FIELD_LABEL_KEY_RE = re.compile(r"^[a-z0-9]+$")
_MAX_FIELD_LABEL_ENTRIES = 256
_MAX_FIELD_LABEL_KEY_CHARS = 64
_MAX_FIELD_LABEL_TEXT_CHARS = 96

# Refactor R1 (plan 125 / M01): orchestration model-stage instruction
# text is declarative content — the same governed versioned-resource
# contract, a different consumer, never a second registry. The
# resource carries text only: instruction ids and lineage versions
# remain typed constants in the application layer, single-sourced.
_ORCH_RESOURCE_ID = "delia.capability_orchestration.instructions"
_ORCH_KIND = "orchestration_instructions"
# v2 (plan 125 adendum): adds the goal/evidence relevance judgment
# stage and the ``relevance_feedback`` argument-block clause.
_ORCH_VERSIONS = frozenset({"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "17", "18", "19", "20", "21", "22", "23", "24", "25", "26"})
_ORCH_KEYS = frozenset(
    {"resource_id", "version", "kind", "owner", "instructions"}
)
_MAX_ORCH_INSTRUCTION_ENTRIES = 32
_MAX_ORCH_INSTRUCTION_BYTES = 8192


class CriInstructionResourceError(Exception):
    """The governed CRI instruction resource is absent or invalid."""

    def __init__(self, code: str, detail: str = "") -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


@dataclass(frozen=True)
class CriInstructionClause:
    """Validated instruction clause — typed content for the consumer."""

    resource_id: str
    version: str
    text: str
    content_hash: str


@dataclass(frozen=True)
class OrchestrationInstructions:
    """Validated orchestration instruction set — declarative text
    keyed by the typed instruction ids (plus the fused
    capability+goal variant key) that remain single-sourced in the
    application layer."""

    resource_id: str
    version: str
    instructions: Mapping[str, str]
    content_hash: str


@dataclass(frozen=True)
class CriPresentationVocabulary:
    """Validated presentation vocabulary — typed sections for the
    response composer."""

    resource_id: str
    version: str
    sections: Mapping[str, Mapping[str, str]]
    content_hash: str
    field_labels: Mapping[str, tuple[str, str, str]] = field(
        default_factory=dict
    )


def _load_resource_object(path: str | Path) -> Mapping:
    """Read + JSON-parse a governed resource — fail closed."""

    try:
        raw = Path(path).read_text(encoding="utf-8")
    except OSError as exc:
        raise CriInstructionResourceError(
            "cri_instruction_resource_unreadable", str(exc)
        ) from exc
    try:
        data = json.loads(raw)
    except ValueError as exc:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid", "not valid JSON"
        ) from exc
    if not isinstance(data, Mapping):
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid", "resource not an object"
        )
    return data


def _validate_identity(
    data: Mapping, *, kind: str, versions: frozenset
) -> str:
    """Shared kind/version gate — returns the validated version."""

    if str(data.get("kind")) != kind:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unknown kind: {data.get('kind')!r}",
        )
    version = str(data.get("version"))
    if version not in versions:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unknown version: {version!r}",
        )
    return version


def load_cri_instruction_clause(path: str | Path) -> CriInstructionClause:
    """Load and validate the governed CRI instruction resource.

    Fail-closed: every deviation — missing file, malformed JSON,
    unsupported or missing fields, unknown kind or version, oversized
    or empty text — raises CriInstructionResourceError. The clause is
    returned whole or not at all.
    """

    data = _load_resource_object(path)
    extra = set(data) - _RESOURCE_KEYS
    if extra:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unsupported fields: {sorted(extra)}",
        )
    missing = {k for k in _REQUIRED_KEYS if not data.get(k)}
    if missing:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"missing fields: {sorted(missing)}",
        )
    version = _validate_identity(
        data, kind=_RESOURCE_KIND, versions=_CLAUSE_VERSIONS
    )
    text = str(data["instruction_text"])
    if not text.strip() or len(text.encode("utf-8")) > (
        _MAX_INSTRUCTION_TEXT_BYTES
    ):
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            "instruction_text empty or oversized",
        )
    return CriInstructionClause(
        resource_id=str(data["resource_id"]),
        version=version,
        text=text,
        content_hash=hashlib.sha256(
            text.encode("utf-8")
        ).hexdigest(),
    )


def _vocabulary_entries(
    value: object, section: str
) -> dict[str, str]:
    """Validate one vocabulary section — bounded str->str entries with
    governed placeholders only."""

    if not isinstance(value, Mapping) or not value:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"section {section!r} missing or not an object",
        )
    entries = dict(value)
    if len(entries) > _MAX_VOCABULARY_SECTION_ENTRIES:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"section {section!r} oversized",
        )
    required = _VOCABULARY_REQUIRED_ENTRIES[section]
    missing = required - set(entries)
    if missing:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"section {section!r} missing entries: {sorted(missing)}",
        )
    out: dict[str, str] = {}
    for key, text in entries.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(text, str)
            or not text.strip()
            or len(text.encode("utf-8")) > _MAX_VOCABULARY_ENTRY_BYTES
        ):
            raise CriInstructionResourceError(
                "cri_instruction_resource_invalid",
                f"section {section!r} invalid entry {key!r}",
            )
        for _, placeholder, _, _ in string.Formatter().parse(text):
            if (
                placeholder is not None
                and placeholder not in _VOCABULARY_PLACEHOLDERS
            ):
                raise CriInstructionResourceError(
                    "cri_instruction_resource_invalid",
                    f"section {section!r} entry {key!r} has unknown "
                    f"placeholder {placeholder!r}",
                )
        out[key] = text
    return out


def _field_label_entries(
    value: object,
) -> dict[str, tuple[str, str, str]]:
    """Validate the optional ``field_labels`` section — a closed map
    of canonical field key → (article, label, suffix) parts.

    Fail-closed like every other section: the section is optional
    (absent → empty map), but when present every key and every part
    is checked — unknown keys or shapes never load partially.
    """

    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            "section 'field_labels' not an object",
        )
    if len(value) > _MAX_FIELD_LABEL_ENTRIES:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            "section 'field_labels' oversized",
        )
    out: dict[str, tuple[str, str, str]] = {}
    for key, entry in value.items():
        if (
            not isinstance(key, str)
            or not _FIELD_LABEL_KEY_RE.match(key)
            or len(key) > _MAX_FIELD_LABEL_KEY_CHARS
            or not isinstance(entry, Mapping)
            or set(entry) != _FIELD_LABEL_PARTS
        ):
            raise CriInstructionResourceError(
                "cri_instruction_resource_invalid",
                f"section 'field_labels' invalid entry {key!r}",
            )
        article, label, suffix = (
            entry["article"], entry["label"], entry["suffix"]
        )
        if (
            article not in _FIELD_LABEL_ARTICLES
            or not isinstance(label, str)
            or not label.strip()
            or not isinstance(suffix, str)
            or not suffix.strip()
            or len(label) > _MAX_FIELD_LABEL_TEXT_CHARS
            or len(suffix) > _MAX_FIELD_LABEL_TEXT_CHARS
            or "{" in label
            or "{" in suffix
        ):
            raise CriInstructionResourceError(
                "cri_instruction_resource_invalid",
                f"section 'field_labels' invalid parts {key!r}",
            )
        out[key] = (article, label, suffix)
    return out


def load_cri_presentation_vocabulary(
    path: str | Path,
) -> CriPresentationVocabulary:
    """Load and validate the governed CRI presentation vocabulary.

    CRI E3: same fail-closed contract as the instruction clause —
    wrong identity/kind/version, extra or missing keys, malformed
    sections, unknown placeholders or oversized entries all raise
    ``CriInstructionResourceError``; the vocabulary is returned whole
    or not at all.
    """

    data = _load_resource_object(path)
    extra = set(data) - _VOCABULARY_KEYS
    if extra:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unsupported fields: {sorted(extra)}",
        )
    if str(data.get("resource_id")) != _VOCABULARY_RESOURCE_ID:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unexpected resource_id: {data.get('resource_id')!r}",
        )
    version = _validate_identity(
        data, kind=_VOCABULARY_KIND, versions=_VOCABULARY_VERSIONS
    )
    field_labels = _field_label_entries(data.get("field_labels"))
    sections = {
        section: _vocabulary_entries(data.get(section), section)
        for section in _VOCABULARY_SECTIONS
    }
    canonical = json.dumps(
        {**sections, "field_labels": field_labels},
        sort_keys=True,
        ensure_ascii=False,
    )
    return CriPresentationVocabulary(
        resource_id=_VOCABULARY_RESOURCE_ID,
        version=version,
        sections=sections,
        content_hash=hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
        field_labels=field_labels,
    )


def load_orchestration_instructions(
    path: str | Path, *, required_names: frozenset[str] | set[str]
) -> OrchestrationInstructions:
    """Load and validate the governed orchestration instruction set.

    Fail-closed like the sibling loaders: wrong identity/kind/version,
    extra or missing top-level keys, a non-mapping ``instructions``
    section, absent/unknown entry names or empty/oversized text all
    raise ``CriInstructionResourceError`` — the set is returned whole
    or not at all. ``required_names`` is supplied by the consumer so
    the application layer stays the single source of the key list.
    """

    data = _load_resource_object(path)
    extra = set(data) - _ORCH_KEYS
    if extra:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unsupported fields: {sorted(extra)}",
        )
    missing = {k for k in _ORCH_KEYS if not data.get(k)}
    if missing:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"missing fields: {sorted(missing)}",
        )
    if str(data.get("resource_id")) != _ORCH_RESOURCE_ID:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unexpected resource_id: {data.get('resource_id')!r}",
        )
    version = _validate_identity(
        data, kind=_ORCH_KIND, versions=_ORCH_VERSIONS
    )
    instructions = data["instructions"]
    if not isinstance(instructions, Mapping):
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            "instructions not an object",
        )
    if len(instructions) > _MAX_ORCH_INSTRUCTION_ENTRIES:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            "instructions oversized",
        )
    names = set(instructions)
    diff = names ^ set(required_names)
    if diff:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"instruction set mismatch: {sorted(diff)}",
        )
    out: dict[str, str] = {}
    for name, text in instructions.items():
        if (
            not isinstance(name, str)
            or not isinstance(text, str)
            or not text.strip()
            or len(text.encode("utf-8")) > _MAX_ORCH_INSTRUCTION_BYTES
        ):
            raise CriInstructionResourceError(
                "cri_instruction_resource_invalid",
                f"instruction {name!r} empty or oversized",
            )
        out[name] = text
    canonical = json.dumps(out, sort_keys=True, ensure_ascii=False)
    return OrchestrationInstructions(
        resource_id=_ORCH_RESOURCE_ID,
        version=version,
        instructions=out,
        content_hash=hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest(),
    )
