"""Layout-only corrective ops. Never changes metric, narrative, or chart family."""

from __future__ import annotations

import copy
import re
from typing import Any, Mapping

from tv_app.application.services.data.design_intelligence_service import (
    DesignIntelligenceService,
)
from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)
from tv_app.application.services.data.slide_auto_layout_service import (
    SlideAutoLayoutService,
)

_REVIEW_RE = re.compile(
    r"(revis\w*|corrig\w*|ajuste(?:\s+o)?\s+layout|safe area|sobreposi\w*|tipografia|fonte pequena|autofix|layout quebrado)",
    re.IGNORECASE,
)
_NEW_CONTENT_RE = re.compile(
    r"\b(adicione|adicionar|crie|criar|novo kpi|nova fonte|nova m[eé]trica|troque a m[eé]trica)\b",
    re.IGNORECASE,
)


class SafeAutoFixService:
    @classmethod
    def is_layout_review(cls, message: str) -> bool:
        return bool(_REVIEW_RE.search(message or ""))

    @classmethod
    def asks_new_content(cls, message: str) -> bool:
        return bool(_NEW_CONTENT_RE.search(message or ""))

    @classmethod
    def ops_for(cls, native_config: Mapping[str, Any] | None) -> list[dict[str, Any]]:
        if not isinstance(native_config, Mapping):
            return []
        audit = DesignIntelligenceService.design_audit(native_config)
        blocks = {
            str(block.get("id")): block
            for block in (native_config.get("blocks") or [])
            if isinstance(block, dict) and block.get("id")
        }
        patches: dict[str, dict[str, Any]] = {}
        margin = _safe_margin()
        for issue in audit.get("issues") or []:
            if not isinstance(issue, dict) or not issue.get("safeAutoFix"):
                continue
            code = str(issue.get("id") or "")
            prefix = code.split(":", 1)[0]
            if prefix in {"block_frame_overflow", "safe_area_violation", "block_frame_non_positive"}:
                for block_id in issue.get("blockIds") or []:
                    _clamp_patch(patches, blocks, str(block_id), margin)
            elif prefix == "block_overlap":
                _overlap_patches(patches, native_config, blocks)
            elif prefix == "part_font_below_min":
                _font_patch(patches, blocks, code)
            elif prefix == "low_contrast":
                for block_id in issue.get("blockIds") or []:
                    _style_patch(patches, blocks, str(block_id), {"color": "#ffffff"})
            elif prefix == "hierarchy_inverted":
                _hierarchy_patch(patches, blocks, code)
        return [
            {"op": "upsert_block", "block": patch}
            for patch in patches.values()
            if patch.get("id") and patch.get("type")
        ]


def _safe_margin() -> float:
    tokens = PresentationRecipeService.document().get("designTokens")
    if not isinstance(tokens, dict):
        return 3.0
    try:
        return float(tokens.get("safeMargin") or 3)
    except (TypeError, ValueError):
        return 3.0


def _patch_for(patches: dict[str, dict[str, Any]], block: Mapping[str, Any]) -> dict[str, Any]:
    block_id = str(block.get("id") or "")
    current = patches.get(block_id)
    if current is None:
        current = {"id": block_id, "type": str(block.get("type") or "")}
        patches[block_id] = current
    return current


def _clamp_patch(
    patches: dict[str, dict[str, Any]],
    blocks: Mapping[str, Mapping[str, Any]],
    block_id: str,
    margin: float,
) -> None:
    block = blocks.get(block_id)
    if not isinstance(block, Mapping):
        return
    frame = block.get("frame") if isinstance(block.get("frame"), dict) else None
    if frame is None:
        return
    try:
        x = float(frame.get("x", 0))
        y = float(frame.get("y", 0))
        w = max(1.0, float(frame.get("w", 1)))
        h = max(1.0, float(frame.get("h", 1)))
    except (TypeError, ValueError):
        return
    limit = 100.0 - (2 * margin)
    w = min(w, limit)
    h = min(h, limit)
    x = min(max(x, margin), 100.0 - margin - w)
    y = min(max(y, margin), 100.0 - margin - h)
    _patch_for(patches, block)["frame"] = {
        "x": round(x, 2),
        "y": round(y, 2),
        "w": round(w, 2),
        "h": round(h, 2),
    }


def _overlap_patches(
    patches: dict[str, dict[str, Any]],
    native_config: Mapping[str, Any],
    blocks: Mapping[str, Mapping[str, Any]],
) -> None:
    clone = copy.deepcopy(dict(native_config))
    SlideAutoLayoutService.apply_kpi_row_if_needed(clone)
    original = {
        str(block.get("id")): block.get("frame")
        for block in (native_config.get("blocks") or [])
        if isinstance(block, dict)
    }
    for block in clone.get("blocks") or []:
        if not isinstance(block, dict) or not block.get("id"):
            continue
        block_id = str(block.get("id"))
        if block.get("frame") != original.get(block_id) and isinstance(block.get("frame"), dict):
            _patch_for(patches, blocks.get(block_id) or block)["frame"] = dict(block["frame"])


def _font_patch(
    patches: dict[str, dict[str, Any]],
    blocks: Mapping[str, Mapping[str, Any]],
    code: str,
) -> None:
    parts = code.split(":")
    if len(parts) < 4:
        return
    block = blocks.get(parts[1])
    if not isinstance(block, Mapping):
        return
    part_name = parts[2]
    minimum = _minimum_from_tail(parts[3])
    if minimum is None:
        return
    patch = _patch_for(patches, block)
    if part_name in {"title", "value"}:
        kpi_parts = patch.setdefault("kpiParts", {})
        part = kpi_parts.setdefault(part_name, {})
        style = part.setdefault("style", {})
        style["fontSize"] = minimum
    elif part_name == "icon":
        kpi_parts = patch.setdefault("kpiParts", {})
        icon = kpi_parts.setdefault("icon", {})
        style = icon.setdefault("style", {})
        style["iconSize"] = minimum


def _hierarchy_patch(
    patches: dict[str, dict[str, Any]],
    blocks: Mapping[str, Mapping[str, Any]],
    code: str,
) -> None:
    parts = code.split(":")
    if len(parts) < 2:
        return
    block = blocks.get(parts[1])
    if not isinstance(block, Mapping):
        return
    kpi = block.get("kpiParts") if isinstance(block.get("kpiParts"), dict) else {}
    title = kpi.get("title") if isinstance(kpi.get("title"), dict) else {}
    title_style = title.get("style") if isinstance(title.get("style"), dict) else {}
    try:
        title_size = float(title_style.get("fontSize") or 18)
    except (TypeError, ValueError):
        title_size = 18
    patch = _patch_for(patches, block)
    value = patch.setdefault("kpiParts", {}).setdefault("value", {}).setdefault("style", {})
    value["fontSize"] = int(title_size) + 8


def _style_patch(
    patches: dict[str, dict[str, Any]],
    blocks: Mapping[str, Mapping[str, Any]],
    block_id: str,
    style: dict[str, Any],
) -> None:
    block = blocks.get(block_id)
    if not isinstance(block, Mapping):
        return
    current = _patch_for(patches, block).setdefault("style", {})
    current.update(style)


def _minimum_from_tail(tail: str) -> int | None:
    if "<" not in tail:
        return None
    raw = tail.split("<", 1)[1]
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return None
