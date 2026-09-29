"""Shared MCP tool metadata / annotation vocabulary (S5).

Owns ONLY the vocabulary-level duplication across the three MCPs:

- the DELPI ToolClass taxonomy actually in use (READ / ANALYSIS / PREPARE /
  ACT — frozen to what apps already register, no speculative classes);
- wire-shaped annotation payloads (SDK-neutral dicts — each app builds the
  ``ToolAnnotations`` object of its own SDK generation);
- DELPI-namespaced ``_meta`` keys (``delpi/securitySchemes``,
  ``delpi/toolClass``) versus the reserved ``securitySchemes`` key both
  current SDK eras legitimately use.

Metadata describes semantics — it NEVER authorizes execution. Backend
AuthZ remains authoritative regardless of hints/classes.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

__all__ = [
    "DELPI_META_SECURITY_SCHEMES",
    "DELPI_META_TOOL_CLASS",
    "SECURITY_SCHEMES_KEY",
    "TOOL_CLASS_ACT",
    "TOOL_CLASS_ANALYSIS",
    "TOOL_CLASS_PREPARE",
    "TOOL_CLASS_READ",
    "delpi_tool_meta",
    "security_schemes_meta",
    "tool_annotations_payload",
]

# Frozen DELPI ToolClass vocabulary — the classes actually registered
# across VISTA/TÉO today. Do not extend without a real consumer.
TOOL_CLASS_READ = "READ"
TOOL_CLASS_ANALYSIS = "ANALYSIS"
TOOL_CLASS_PREPARE = "PREPARE"
TOOL_CLASS_ACT = "ACT"

# Reserved wire key both SDK generations accept as typed securitySchemes.
SECURITY_SCHEMES_KEY = "securitySchemes"

# DELPI-namespaced _meta keys (VISTA wire — bare `securitySchemes` inside
# `_meta` is reserved and broke OpenAI discovery; keep namespaced forms).
DELPI_META_SECURITY_SCHEMES = "delpi/securitySchemes"
DELPI_META_TOOL_CLASS = "delpi/toolClass"


def tool_annotations_payload(
    title: str,
    *,
    read_only: bool,
    destructive: bool,
    idempotent: bool | None = None,
    open_world: bool = False,
) -> dict[str, Any]:
    """Wire-shaped annotation payload — SDK-neutral dict.

    Apps pass it through ``ToolAnnotations.model_validate(...)`` of their
    own SDK generation (mcp 1.30 camelCase vs 2.x snake-case kwargs differ;
    both accept wire aliases on validation). Hints describe semantics only
    — they never grant permission.
    """
    payload: dict[str, Any] = {
        "title": title,
        "readOnlyHint": read_only,
        "destructiveHint": destructive,
        "openWorldHint": open_world,
    }
    if idempotent is not None:
        payload["idempotentHint"] = idempotent
    return payload


def delpi_tool_meta(
    *,
    tool_class: str,
    security_schemes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """DELPI-namespaced ``_meta`` payload (VISTA strategy)."""
    return {
        DELPI_META_SECURITY_SCHEMES: list(security_schemes),
        DELPI_META_TOOL_CLASS: tool_class,
    }


def security_schemes_meta(
    security_schemes: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reserved ``securitySchemes`` meta payload (TÉO/DAVI strategy)."""
    return {SECURITY_SCHEMES_KEY: list(security_schemes)}
