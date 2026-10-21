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
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

_RESOURCE_KIND = "instruction_clause"
_KNOWN_VERSIONS = frozenset({"1"})
_RESOURCE_KEYS = frozenset(
    {"resource_id", "version", "kind", "owner", "instruction_text"}
)
_REQUIRED_KEYS = _RESOURCE_KEYS
_MAX_INSTRUCTION_TEXT_BYTES = 4096


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


def load_cri_instruction_clause(path: str | Path) -> CriInstructionClause:
    """Load and validate the governed CRI instruction resource.

    Fail-closed: every deviation — missing file, malformed JSON,
    unsupported or missing fields, unknown kind or version, oversized
    or empty text — raises CriInstructionResourceError. The clause is
    returned whole or not at all.
    """

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
    if str(data["kind"]) != _RESOURCE_KIND:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unknown kind: {data['kind']!r}",
        )
    version = str(data["version"])
    if version not in _KNOWN_VERSIONS:
        raise CriInstructionResourceError(
            "cri_instruction_resource_invalid",
            f"unknown version: {version!r}",
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
