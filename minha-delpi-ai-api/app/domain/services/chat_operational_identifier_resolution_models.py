"""Modelos de resolução tipada de identificadores operacionais."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

IdentifierRole = Literal[
    "delpi_product_code",
    "supplier_part_number",
    "unknown",
]

IdentifierSource = Literal[
    "message_hint",
    "session_focus",
    "format_heuristic",
    "none",
]

IdentifierAmbiguity = Literal[
    "none",
    "multiple_same_role",
    "mixed_roles",
    "unknown_role",
]


@dataclass(frozen=True, slots=True)
class IdentifierResolution:
    value: str
    role: IdentifierRole
    confidence: float
    source: IdentifierSource
    span: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class IdentifierResolutionSet:
    items: tuple[IdentifierResolution, ...] = ()
    primary: IdentifierResolution | None = None
    ambiguity: IdentifierAmbiguity = "none"

    def role_values(self, role: IdentifierRole) -> tuple[str, ...]:
        return tuple(item.value for item in self.items if item.role == role)
