"""Deployable VISTA agent intelligence (not GPT Builder Instructions).

Loaded from ``vista_agent_intelligence.json`` and projected on
``get_catalog`` → ``capability_surface.agent_directives`` so behavior
evolves with API deploy without re-pasting Builder Instructions.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

CONTENT_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "vista_agent_intelligence.json"
)


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_vista_agent_intelligence_cache() -> None:
    _load.cache_clear()


_LIST_CAP_KEYS = frozenset({"examples", "examplePrompts", "anti_patterns", "forbidden", "when"})
_MAX_LIST_ITEMS = 10
# Keep connector + filter/layout anti-patterns; catalog budget still owns the ceiling.
_MAX_ANTI_PATTERNS = 48
# Keys that are prose duplicates of principle+rules — drop to save Actions budget.
_DROP_DIRECTIVE_KEYS = frozenset({"summary", "example", "examples", "examplePrompts"})


_GPT_NAME_RE = re.compile(r"gpt_[a-z_]+")
_PAREN_RE = re.compile(r"\(([^()]*)\)")


def _strip_actions_annotations(text: str) -> str:
    """Remove ``Actions:``-labeled segments inside parentheses, preserving any
    other semantic content in the same group."""

    def _fix(match: re.Match) -> str:
        parts = [p.strip() for p in match.group(1).split(";")]
        kept = [p for p in parts if not p.lower().startswith("actions")]
        return "(" + "; ".join(kept) + ")" if kept else ""

    text = _PAREN_RE.sub(_fix, text)
    return re.sub(r"\s+([.,;:!?])", r"\1", text)


def _neutralize_for_mcp(node: Any, *, _skip_keys: frozenset = frozenset({"surface_parity"})) -> Any:
    """Neutralize Actions-adapter annotations for the MCP projection.

    ``(Actions: ...)``/``(Actions ...)`` parentheticals name adapter mechanics
    and are dropped; any residual ``gpt_*`` token is rewritten through the
    canonical parity map to its neutral name. The ``surface_parity`` registry
    itself is exempt — its gpt_* keys ARE the canonical Actions-name record.
    """
    if isinstance(node, dict):
        return {
            k: (v if k in _skip_keys else _neutralize_for_mcp(v))
            for k, v in node.items()
        }
    if isinstance(node, list):
        return [_neutralize_for_mcp(item) for item in node]
    if isinstance(node, str):
        text = _strip_actions_annotations(node)
        mapping = {
            actions: neutral
            for actions, neutral in (
                VistaAgentIntelligenceService.document().get("surface_parity") or {}
            ).get("parity_map", {}).items()
        }
        return _GPT_NAME_RE.sub(lambda m: mapping.get(m.group(0), m.group(0)), text)
    return node


def _compact_for_actions(node: Any, *, key: str | None = None) -> Any:
    """Drop example/summary blobs; keep directive contracts for Actions budget."""
    if isinstance(node, dict):
        out: dict[str, Any] = {}
        for child_key, value in node.items():
            if child_key in _DROP_DIRECTIVE_KEYS:
                continue
            out[str(child_key)] = _compact_for_actions(value, key=str(child_key))
        return out
    if isinstance(node, list):
        if key == "anti_patterns":
            trimmed = node[:_MAX_ANTI_PATTERNS]
        elif key in _LIST_CAP_KEYS:
            trimmed = node[:_MAX_LIST_ITEMS]
        else:
            trimmed = node
        return [_compact_for_actions(item, key=key) for item in trimmed]
    return node


class VistaAgentIntelligenceService:
    @classmethod
    def document(cls) -> dict[str, Any]:
        raw = _load()
        return raw if isinstance(raw, dict) else {}

    @classmethod
    def version(cls) -> str:
        return str(cls.document().get("version") or "").strip()

    @classmethod
    def agent_directives(cls, *, transport: str = "mcp") -> dict[str, Any]:
        """Compact directives for the external specialist to obey at runtime.

        ``transport="mcp"`` projects the full document (MCP-primary surface:
        ``surface_parity`` + ``write_flow_mcp`` included). ``transport="actions"``
        drops the MCP-facing sections — the GPT Actions envelope sits at the
        ~100 KiB OpenAI ceiling and its own tool names are already ``gpt_*``.
        """
        from tv_app.application.services.data.presentation_recipe_service import (
            PresentationRecipeService,
        )

        doc = cls.document()
        recipes = doc.get("presentation_recipes") or {}
        if isinstance(recipes, dict) and not recipes.get("catalog"):
            # Live catalog of recipe ids/markers — Actions-budget projection
            # (full tokens stay in presentation_recipes.json for server/VERIFY).
            recipes = {
                **recipes,
                "catalog": PresentationRecipeService.catalog_projection_for_actions(),
            }
        raw = {
            "version": cls.version(),
            "authority": (
                "Obey these directives from live get_catalog "
                "(Actions: gpt_get_catalog). "
                "They override stale Builder Knowledge for mutation behavior."
            ),
            "execution_posture": doc.get("execution_posture") or {},
            "actions_runtime": doc.get("actions_runtime") or {},
            "continuous_review": doc.get("continuous_review") or {},
            "visual_impact": doc.get("visual_impact") or {},
            "visual_selection": doc.get("visual_selection") or {},
            "composed_visuals": doc.get("composed_visuals") or {},
            "shape_chrome": doc.get("shape_chrome") or {},
            "object_resolution": doc.get("object_resolution") or {},
            "editor_focus": doc.get("editor_focus") or {},
            "playlist_curation": doc.get("playlist_curation") or {},
            "branch_scope": doc.get("branch_scope") or {},
            "filter_layering": doc.get("filter_layering") or {},
            "param_expressions": doc.get("param_expressions") or {},
            "slide_craft": doc.get("slide_craft") or {},
            "si_goals": doc.get("si_goals") or {},
            "write_quality": doc.get("write_quality") or {},
            "slide_design": doc.get("slide_design") or {},
            "screenshot_parity": doc.get("screenshot_parity") or {},
            "layout_perception": doc.get("layout_perception") or {},
            "visual_verification": doc.get("visual_verification") or {},
            "data_discovery": doc.get("data_discovery") or {},
            "data_transform": doc.get("data_transform") or {},
            # DM4 — DataModel-first + migração legacy explícita.
            "data_model": doc.get("data_model") or {},
            "compound_slide": doc.get("compound_slide") or {},
            "display_format": doc.get("display_format") or {},
            "presentation_recipes": recipes,
            "media_limits": doc.get("media_limits") or {},
            "brand_logo": doc.get("brand_logo") or {},
            "published_templates": doc.get("published_templates") or {},
            "mcp_delia": doc.get("mcp_delia") or {},
            "modes": doc.get("modes") or {},
            # Actions write-flow variant (commit_now/confirmation.confirmed
            # semantics) — labeled `surface: gpt_actions` in the JSON document.
            "write_flow": doc.get("write_flow") or {},
            # MCP3 — projected now that the shared directives are
            # transport-neutral: parity map + MCP-primary governed envelope.
            "surface_parity": doc.get("surface_parity") or {},
            "write_flow_mcp": doc.get("write_flow_mcp") or {},
            "anti_patterns": list(doc.get("anti_patterns") or []),
            "auth_errors": doc.get("auth_errors") or {},
        }
        if transport == "actions":
            # Actions stays inside the ~100 KiB OpenAI ceiling: MCP-facing
            # sections are projected for the MCP transport only, and the
            # write_flow surface labels are noise for the Actions specialist.
            raw.pop("surface_parity", None)
            raw.pop("write_flow_mcp", None)
            raw.pop("mcp_delia", None)
            # Expression contract is MCP-primary: the Actions envelope sits at
            # the ~100 KiB OpenAI ceiling with no residual budget.
            raw.pop("param_expressions", None)
            write_flow = raw.get("write_flow")
            if isinstance(write_flow, dict):
                write_flow.pop("surface", None)
                write_flow.pop("note", None)
        else:
            # MCP never receives Actions-envelope semantics: surface/note/
            # additive/destructive label or describe gpt_* operations and
            # commit_now/confirmation.confirmed, which exist only on the
            # Actions transport. Neutral policy keys (compound, same_turn,
            # refuse_only_when, forbidden_handles) stay — write_flow_mcp is
            # the MCP-primary governed envelope.
            write_flow = raw.get("write_flow")
            if isinstance(write_flow, dict):
                for key in ("surface", "note", "additive", "destructive"):
                    write_flow.pop(key, None)
            raw = _neutralize_for_mcp(raw)
        return _compact_for_actions(raw)
