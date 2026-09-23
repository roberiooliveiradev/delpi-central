"""Auto-layout KPIs when a batch leaves default/overlapping frames."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})
_CHART_TYPES = frozenset({"chart_view", "data_chart"})
_TABLE_TYPES = frozenset({"table_view", "data_table"})
_INPUT_TYPES = frozenset({"input"})

_RECIPE_BY_COUNT = {
    2: "TV_KPI_ROW_2",
    3: "TV_KPI_ROW_3",
    4: "TV_KPI_GRID_4",
}


def _frame_tuple(frame: dict[str, Any] | None) -> tuple[float, float, float, float] | None:
    if not isinstance(frame, dict):
        return None
    try:
        return (
            float(frame.get("x", 0)),
            float(frame.get("y", 0)),
            float(frame.get("w", 0)),
            float(frame.get("h", 0)),
        )
    except (TypeError, ValueError):
        return None


class SlideAutoLayoutService:
    """Redistribute KPI frames from typed recipes when N defaults collide."""

    @classmethod
    def recipe_kpi_frames(cls, recipe_id: str) -> list[dict[str, float]]:
        frames: list[dict[str, float]] = []
        for op in PresentationRecipeService.ops_for_recipe(recipe_id):
            if str(op.get("op") or "") != "upsert_block":
                continue
            block = op.get("block")
            if not isinstance(block, dict):
                continue
            if str(block.get("type") or "") not in _KPI_TYPES:
                continue
            fr = block.get("frame")
            if isinstance(fr, dict):
                frames.append(
                    {
                        "x": float(fr.get("x", 0)),
                        "y": float(fr.get("y", 0)),
                        "w": float(fr.get("w", 0)),
                        "h": float(fr.get("h", 0)),
                    }
                )
        return frames

    @classmethod
    def apply_kpi_row_if_needed(
        cls,
        native_config: dict[str, Any],
        *,
        informed_block_ids: set[str] | None = None,
    ) -> bool:
        """Mutate cfg in place. Returns True if frames changed.

        Never overwrites frames for block ids in ``informed_block_ids``.
        """
        blocks = native_config.get("blocks")
        if not isinstance(blocks, list):
            return False
        informed = informed_block_ids or set()
        kpis: list[dict[str, Any]] = []
        for block in blocks:
            if not isinstance(block, dict):
                continue
            if str(block.get("type") or "") not in _KPI_TYPES:
                continue
            bid = str(block.get("id") or "").strip()
            if bid and bid in informed:
                continue
            kpis.append(block)
        n = len(kpis)
        recipe_id = _RECIPE_BY_COUNT.get(n)
        if not recipe_id:
            return False
        target_frames = cls.recipe_kpi_frames(recipe_id)
        if len(target_frames) != n:
            return False

        # Only redistribute when frames are missing/identical/default-ish (same x,y).
        positions = [_frame_tuple(b.get("frame") if isinstance(b.get("frame"), dict) else None) for b in kpis]
        if all(p is not None for p in positions):
            unique = {p for p in positions if p is not None}
            # Distinct non-overlapping layout already present → leave alone.
            if len(unique) == n:
                xs = sorted(p[0] for p in unique)
                # If all share same x and y → collide; else assume intentional.
                same_origin = len({(p[0], p[1]) for p in unique}) == 1
                if not same_origin:
                    return False

        changed = False
        for block, frame in zip(kpis, target_frames):
            current = block.get("frame") if isinstance(block.get("frame"), dict) else {}
            next_frame = {**current, **frame}
            if current != next_frame:
                block["frame"] = next_frame
                changed = True
        return changed

    @classmethod
    def _recipe_frames_by_type(
        cls,
        recipe_id: str,
        types: frozenset[str],
    ) -> dict[str, dict[str, float]]:
        out: dict[str, dict[str, float]] = {}
        for op in PresentationRecipeService.ops_for_recipe(recipe_id):
            if str(op.get("op") or "") != "upsert_block":
                continue
            block = op.get("block")
            if not isinstance(block, dict):
                continue
            btype = str(block.get("type") or "")
            if btype not in types:
                continue
            fr = block.get("frame")
            if isinstance(fr, dict) and btype not in out:
                out[btype] = {
                    "x": float(fr.get("x", 0)),
                    "y": float(fr.get("y", 0)),
                    "w": float(fr.get("w", 0)),
                    "h": float(fr.get("h", 0)),
                }
        return out

    @classmethod
    def _blocks_collide(cls, blocks: list[dict[str, Any]]) -> bool:
        positions = [
            _frame_tuple(b.get("frame") if isinstance(b.get("frame"), dict) else None)
            for b in blocks
        ]
        positions = [p for p in positions if p is not None]
        if len(positions) < 2:
            return False
        unique = {p for p in positions}
        if len(unique) == 1:
            return True
        if len(unique) == len(positions):
            xs = sorted(p[0] for p in unique)
            if len({(p[0], p[1]) for p in unique}) == 1:
                return True
        return len(unique) < len(positions)

    @classmethod
    def _apply_recipe_frames(
        cls,
        blocks: list[dict[str, Any]],
        recipe_id: str,
        types: frozenset[str],
        *,
        informed_block_ids: set[str],
    ) -> bool:
        templates = cls._recipe_frames_by_type(recipe_id, types)
        if not templates:
            return False
        changed = False
        for block in blocks:
            btype = str(block.get("type") or "")
            if btype not in types:
                continue
            bid = str(block.get("id") or "").strip()
            if bid and bid in informed_block_ids:
                continue
            frame = templates.get(btype)
            if not frame:
                continue
            current = block.get("frame") if isinstance(block.get("frame"), dict) else {}
            next_frame = {**current, **frame}
            if current != next_frame:
                block["frame"] = next_frame
                changed = True
        return changed

    @classmethod
    def _redistribute_input_strip(
        cls,
        blocks: list[dict[str, Any]],
        *,
        informed_block_ids: set[str],
    ) -> bool:
        inputs = [
            b
            for b in blocks
            if isinstance(b, dict)
            and str(b.get("type") or "") in _INPUT_TYPES
            and str(b.get("id") or "").strip() not in informed_block_ids
        ]
        if len(inputs) < 2:
            return False
        gutter = 2.0
        total_w = 100.0 - gutter * (len(inputs) + 1)
        slice_w = total_w / len(inputs)
        y = 82.0
        h = 10.0
        changed = False
        for index, block in enumerate(inputs):
            x = gutter + index * (slice_w + gutter)
            next_frame = {"x": x, "y": y, "w": slice_w, "h": h}
            current = block.get("frame") if isinstance(block.get("frame"), dict) else {}
            merged = {**current, **next_frame}
            if current != merged:
                block["frame"] = merged
                changed = True
        return changed

    @classmethod
    def apply_post_create_layout(
        cls,
        native_config: dict[str, Any],
        *,
        informed_block_ids: set[str] | None = None,
    ) -> bool:
        """KPI row + chart/table recipes + filter strip redistribution."""
        changed = cls.apply_kpi_row_if_needed(
            native_config,
            informed_block_ids=informed_block_ids,
        )
        informed = informed_block_ids or set()
        blocks = native_config.get("blocks")
        if not isinstance(blocks, list):
            return changed
        spatial = [b for b in blocks if isinstance(b, dict)]
        charts = [b for b in spatial if str(b.get("type") or "") in _CHART_TYPES]
        tables = [b for b in spatial if str(b.get("type") or "") in _TABLE_TYPES]
        kpis = [b for b in spatial if str(b.get("type") or "") in _KPI_TYPES]
        if len(charts) == 1 and len(tables) == 1:
            targets = charts + tables
            if cls._blocks_collide(targets):
                if cls._apply_recipe_frames(
                    spatial,
                    "TV_KPI_SERIES_TABLE",
                    _CHART_TYPES | _TABLE_TYPES,
                    informed_block_ids=informed,
                ):
                    changed = True
        elif len(charts) == 1 and len(kpis) == 1 and not tables:
            targets = charts + kpis
            if cls._blocks_collide(targets):
                if cls._apply_recipe_frames(
                    spatial,
                    "TV_KPI_PLUS_CHART",
                    _CHART_TYPES | _KPI_TYPES,
                    informed_block_ids=informed,
                ):
                    changed = True
        if cls._redistribute_input_strip(spatial, informed_block_ids=informed):
            changed = True
        return changed
