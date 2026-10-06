"""Transport projection for TÉO capability/intelligence payloads.

Canonical capability/parity record:
``tm_app.application.intelligence.capability_registry`` — this module only
*derives* per-transport projections from it; it never re-defines operation
names or write semantics and never imports a transport adapter.

Transports:

- ``"gpt_actions"`` — Actions surface (``gpt_*`` operationIds, additive
  ``commit_now`` policy). Byte-compatible with the historical contract.
- ``"mcp"`` — MCP surface (``prepare_*`` / ``commit_proposal`` only).
  PREPARE is pure: no ``commit_now``, no atomic prepare+commit, every
  material write requires ``commit_proposal`` with explicit confirmation
  and backend AuthZ.

Fail closed: an unknown ``gpt_*`` name or a residual ``commit_now`` token
in the MCP projection raises :class:`ProjectionContractError`. Only the
explicitly listed legacy tombstones render as ``removed_*`` markers.
"""

from __future__ import annotations

import re
from typing import Any

from tm_app.application.intelligence.capability_registry import (
    ProjectionContractError,
    actions_to_mcp_primary,
)

__all__ = [
    "actions_to_mcp_primary",
    "neutralize_for_mcp",
    "MCP_DROP_KEYS",
]

_GPT_NAME_RE = re.compile(r"gpt_[a-z_]+")
_PAREN_RE = re.compile(r"\(([^()]*)\)")

# Actions-only sections/keys never projected to MCP.
MCP_DROP_KEYS = frozenset(
    {
        "gpt_operations",
        "gpt",
        "commit_now",
        "commit_now_parameter",
        "legacy_removed_from_builder",
        "rules_actions",
        "forbidden_actions",
        "anti_patterns_actions",
    }
)

_MCP_KEY_REWRITE = {
    "gpt_governed_parity": "governed_parity",
    "gpt_actions": "actions",
}

# Pipeline/policy tokens that encode the Actions atomic prepare+commit path.
# On MCP every write is PREPARE → explicit confirmation → commit_proposal.
_MCP_TOKEN_REWRITE = {
    "commit_now_or_confirm": "confirm_then_commit_proposal",
    "commit_now_if_additive": "confirm_then_commit_proposal",
    "commit_now_additive": "confirm_then_commit_proposal",
    "commit_now_allowed_additive": "explicit_confirmation_required",
    "create_update_duplicate_commit_now_delete_confirm": (
        "explicit_confirmation_before_commit"
    ),
    "crud_additive_commit_now_workflow_confirm": (
        "explicit_confirmation_before_commit"
    ),
    "mixed_cost_allows_commit_now": "explicit_confirmation_before_commit",
    "explicit_confirmation_required_no_commit_now": (
        "explicit_confirmation_required"
    ),
}

# Known non-callable ``gpt_*`` names → neutral MCP rendering. Explicit,
# enumerable tombstones only — UNKNOWN names raise ProjectionContractError.
_MCP_KNOWN_TOMBSTONES = {
    "gpt_actions": "actions",  # sibling surface name (availability flags)
    "gpt_create_record": "removed_legacy_create_record",
    "gpt_update_record": "removed_legacy_update_record",
    "gpt_delete_record": "removed_legacy_delete_record",
    "gpt_duplicate_record": "removed_legacy_duplicate_record",
    "gpt_commit_improvement_package": "removed_legacy_package_commit",
}


def _strip_actions_annotations(text: str) -> str:
    """Remove ``(Actions: ...)``-labeled segments inside parentheses, preserving
    any other semantic content in the same group."""

    def _fix(match: re.Match) -> str:
        parts = [p.strip() for p in match.group(1).split(";")]
        kept = [p for p in parts if not p.lower().startswith("actions")]
        return "(" + "; ".join(kept) + ")" if kept else ""

    text = _PAREN_RE.sub(_fix, text)
    return re.sub(r"\s+([.,;:!?])", r"\1", text)


def _neutralize_text_for_mcp(text: str) -> str:
    text = _strip_actions_annotations(text)
    mapping = actions_to_mcp_primary()

    def _sub(match: re.Match) -> str:
        name = match.group(0)
        resolved = mapping.get(name) or _MCP_KNOWN_TOMBSTONES.get(name)
        if resolved is None:
            raise ProjectionContractError(
                f"Unknown gpt_* name '{name}' in MCP projection — "
                "no parity binding and not a registered legacy tombstone.",
                detail={"name": name},
            )
        return resolved

    text = _GPT_NAME_RE.sub(_sub, text)
    for token, replacement in _MCP_TOKEN_REWRITE.items():
        text = text.replace(token, replacement)
    if "commit_now" in text or _GPT_NAME_RE.search(text):
        raise ProjectionContractError(
            "Residual Actions semantics after MCP neutralization.",
            detail={"fragment": text[:200]},
        )
    return text


def neutralize_for_mcp(node: Any) -> Any:
    """Project residual descriptive prose onto the MCP transport.

    Used ONLY for descriptive prose/labels — never for capability identity
    (structured projections resolve names through the capability registry).
    Drops Actions-only keys, strips ``(Actions: ...)`` annotations, rewrites
    ``gpt_*`` names through the canonical parity map, and rewrites
    pipeline/policy tokens that encode the atomic prepare+commit path.
    Any unmapped name or residual ``commit_now`` fails closed.
    """
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for key, value in node.items():
            if key in MCP_DROP_KEYS:
                continue
            out[_MCP_KEY_REWRITE.get(key, key)] = neutralize_for_mcp(value)
        return out
    if isinstance(node, list):
        return [neutralize_for_mcp(item) for item in node]
    if isinstance(node, str):
        return _neutralize_text_for_mcp(node)
    return node
