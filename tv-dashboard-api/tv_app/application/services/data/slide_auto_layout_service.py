"""Auto-layout KPIs when a batch leaves default/overlapping frames."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.presentation_recipe_service import (
    PresentationRecipeService,
)

_KPI_TYPES = frozenset({"kpi_view", "data_kpi"})

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
