"""Transport projection for TÉO capability/intelligence payloads.

Canonical parity record: ``tm_app.interface.mcp.constants.GPT_TO_MCP_TOOLS``
(owner: the MCP contract surface). This module derives per-transport
projections — it never re-defines operation names or write semantics.

Transports:

- ``"gpt_actions"`` — Actions surface (``gpt_*`` operationIds, additive
  ``commit_now`` policy). Byte-compatible with the historical contract.
- ``"mcp"`` — MCP surface (``prepare_*`` / ``commit_proposal`` only).
  PREPARE is pure: no ``commit_now``, no atomic prepare+commit, every
  material write requires ``commit_proposal`` with explicit confirmation
  and backend AuthZ.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Any

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

# Known non-callable ``gpt_*`` names → neutral MCP rendering: removed legacy
# Actions ops become tombstones; ``gpt_actions`` is the sibling surface name.
_MCP_REMOVED_OPS = {
    "gpt_actions": "actions",
    "gpt_create_record": "removed_legacy_create_record",
    "gpt_update_record": "removed_legacy_update_record",
    "gpt_delete_record": "removed_legacy_delete_record",
    "gpt_duplicate_record": "removed_legacy_duplicate_record",
    "gpt_commit_improvement_package": "removed_legacy_package_commit",
}


@lru_cache(maxsize=1)
def actions_to_mcp_primary() -> dict[str, str]:
    """``gpt_*`` operationId → primary MCP tool name (canonical parity record)."""
    from tm_app.interface.mcp.constants import GPT_TO_MCP_TOOLS

    mapping: dict[str, str] = {}
    for gpt_op, tools in GPT_TO_MCP_TOOLS.items():
        suffix = gpt_op.removeprefix("gpt_")
        primary = next((t for t in tools if t.endswith(suffix)), None)
        if primary is None:
            primary = next((t for t in tools if t.startswith("prepare_")), tools[0])
        mapping[gpt_op] = primary
    return mapping


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
        return mapping.get(name) or _MCP_REMOVED_OPS.get(name) or (
            "removed_actions_operation"
        )

    text = _GPT_NAME_RE.sub(_sub, text)
    for token, replacement in _MCP_TOKEN_REWRITE.items():
        text = text.replace(token, replacement)
    return text


def neutralize_for_mcp(node: Any) -> Any:
    """Project an Actions-shaped payload onto the MCP transport.

    Drops Actions-only keys, strips ``(Actions: ...)`` annotations, rewrites
    ``gpt_*`` operation names through the canonical parity map (unknown names
    become ``removed_actions_operation`` tombstones), and rewrites pipeline/
    policy tokens that encode the atomic prepare+commit path.
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
