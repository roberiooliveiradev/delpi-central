"""Canonical geometry layout for PresentationMutation (align / distribute / z-order).

Ports the editor algorithms from ``comunicadoLayoutAlign`` / z-order helpers so
VISTA and the MFE share one owner. Units are simple block frames (grouping is
expanded by the caller via blockIds).
"""

from __future__ import annotations

from typing import Any, Literal

LayoutAlignCommand = Literal[
    "align-left",
    "align-center-h",
    "align-right",
    "align-top",
    "align-center-v",
    "align-bottom",
    "distribute-h",
    "distribute-v",
    "align-slide-left",
    "align-slide-center-h",
    "align-slide-right",
    "align-slide-top",
    "align-slide-center-v",
    "align-slide-bottom",
]

ZOrderCommand = Literal[
    "bring-to-front",
    "send-to-back",
    "bring-forward",
    "send-backward",
]

SLIDE_BOUNDS = {"x": 0.0, "y": 0.0, "w": 100.0, "h": 100.0}

_ALIGN_COMMANDS = frozenset(
    {
        "align-left",
        "align-center-h",
        "align-right",
        "align-top",
        "align-center-v",
        "align-bottom",
        "distribute-h",
        "distribute-v",
        "align-slide-left",
        "align-slide-center-h",
        "align-slide-right",
        "align-slide-top",
        "align-slide-center-v",
        "align-slide-bottom",
    }
)


def _frame_of(block: dict[str, Any]) -> dict[str, float] | None:
    frame = block.get("frame")
    if not isinstance(frame, dict):
        return None
    try:
        return {
            "x": float(frame.get("x", 0)),
            "y": float(frame.get("y", 0)),
            "w": float(frame.get("w", 0)),
            "h": float(frame.get("h", 0)),
        }
    except (TypeError, ValueError):
        return None


def _set_frame_xy(block: dict[str, Any], *, x: float, y: float) -> None:
    frame = block.get("frame")
    if not isinstance(frame, dict):
        frame = {}
        block["frame"] = frame
    prev_x = float(frame.get("x", 0) or 0)
    prev_y = float(frame.get("y", 0) or 0)
    dx = x - prev_x
    dy = y - prev_y
    frame["x"] = x
    frame["y"] = y
    # Keep line vertices in sync when present (shape lines).
    vertices = block.get("vertices")
    if isinstance(vertices, list) and (dx or dy):
        next_verts: list[Any] = []
        for point in vertices:
            if not isinstance(point, dict):
                next_verts.append(point)
                continue
            try:
                next_verts.append(
                    {
                        **point,
                        "x": float(point.get("x", 0)) + dx,
                        "y": float(point.get("y", 0)) + dy,
                    }
                )
            except (TypeError, ValueError):
                next_verts.append(point)
        block["vertices"] = next_verts


def align_blocks(
    blocks: list[dict[str, Any]],
    block_ids: list[str],
    command: str,
    *,
    slide_bounds: dict[str, float] | None = None,
) -> list[str]:
    """Mutate frames in place. Returns ids whose geometry changed."""
    cmd = str(command or "").strip()
    if cmd not in _ALIGN_COMMANDS:
        raise ValueError(f"Comando de layout inválido: {command}")

    id_set = {str(i).strip() for i in block_ids if str(i).strip()}
    targets: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        bid = str(block.get("id") or "").strip()
        if bid not in id_set:
            continue
        if _frame_of(block) is None:
            continue
        targets.append(block)

    if not targets:
        return []

    slide = slide_bounds or SLIDE_BOUNDS
    changed: list[str] = []

    def _mark(block: dict[str, Any], x: float, y: float) -> None:
        fr = _frame_of(block)
        if fr is None:
            return
        if abs(fr["x"] - x) < 1e-9 and abs(fr["y"] - y) < 1e-9:
            return
        _set_frame_xy(block, x=x, y=y)
        changed.append(str(block.get("id") or ""))

    if cmd.startswith("align-slide-"):
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            if cmd == "align-slide-left":
                _mark(block, slide["x"], fr["y"])
            elif cmd == "align-slide-right":
                _mark(block, slide["x"] + slide["w"] - fr["w"], fr["y"])
            elif cmd == "align-slide-center-h":
                _mark(block, slide["x"] + (slide["w"] - fr["w"]) / 2, fr["y"])
            elif cmd == "align-slide-top":
                _mark(block, fr["x"], slide["y"])
            elif cmd == "align-slide-bottom":
                _mark(block, fr["x"], slide["y"] + slide["h"] - fr["h"])
            elif cmd == "align-slide-center-v":
                _mark(block, fr["x"], slide["y"] + (slide["h"] - fr["h"]) / 2)
        return [c for c in changed if c]

    if cmd in {"distribute-h", "distribute-v"}:
        if len(targets) < 3:
            return []
    elif len(targets) < 2:
        return []

    if cmd == "align-left":
        min_x = min(_frame_of(b)["x"] for b in targets)  # type: ignore[index]
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, min_x, fr["y"])
    elif cmd == "align-right":
        max_right = max(_frame_of(b)["x"] + _frame_of(b)["w"] for b in targets)  # type: ignore[index]
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, max_right - fr["w"], fr["y"])
    elif cmd == "align-center-h":
        min_x = min(_frame_of(b)["x"] for b in targets)  # type: ignore[index]
        max_right = max(_frame_of(b)["x"] + _frame_of(b)["w"] for b in targets)  # type: ignore[index]
        center = (min_x + max_right) / 2
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, center - fr["w"] / 2, fr["y"])
    elif cmd == "align-top":
        min_y = min(_frame_of(b)["y"] for b in targets)  # type: ignore[index]
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, fr["x"], min_y)
    elif cmd == "align-bottom":
        max_bottom = max(_frame_of(b)["y"] + _frame_of(b)["h"] for b in targets)  # type: ignore[index]
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, fr["x"], max_bottom - fr["h"])
    elif cmd == "align-center-v":
        min_y = min(_frame_of(b)["y"] for b in targets)  # type: ignore[index]
        max_bottom = max(_frame_of(b)["y"] + _frame_of(b)["h"] for b in targets)  # type: ignore[index]
        center = (min_y + max_bottom) / 2
        for block in targets:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, fr["x"], center - fr["h"] / 2)
    elif cmd == "distribute-h":
        sorted_blocks = sorted(targets, key=lambda b: _frame_of(b)["x"])  # type: ignore[index]
        first = _frame_of(sorted_blocks[0])
        last = _frame_of(sorted_blocks[-1])
        assert first and last
        span = last["x"] + last["w"] - first["x"]
        total_w = sum(_frame_of(b)["w"] for b in sorted_blocks)  # type: ignore[index]
        gap = (span - total_w) / (len(sorted_blocks) - 1)
        cursor = first["x"]
        for block in sorted_blocks:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, cursor, fr["y"])
            cursor += fr["w"] + gap
    elif cmd == "distribute-v":
        sorted_blocks = sorted(targets, key=lambda b: _frame_of(b)["y"])  # type: ignore[index]
        first = _frame_of(sorted_blocks[0])
        last = _frame_of(sorted_blocks[-1])
        assert first and last
        span = last["y"] + last["h"] - first["y"]
        total_h = sum(_frame_of(b)["h"] for b in sorted_blocks)  # type: ignore[index]
        gap = (span - total_h) / (len(sorted_blocks) - 1)
        cursor = first["y"]
        for block in sorted_blocks:
            fr = _frame_of(block)
            assert fr is not None
            _mark(block, fr["x"], cursor)
            cursor += fr["h"] + gap

    return [c for c in changed if c]


def _style_z(block: dict[str, Any]) -> int:
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    try:
        return int(style.get("zIndex", 0) or 0)
    except (TypeError, ValueError):
        return 0


def _set_z(block: dict[str, Any], z: int) -> None:
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    style = dict(style)
    style["zIndex"] = int(z)
    block["style"] = style


def reorder_block_z(
    blocks: list[dict[str, Any]],
    block_ids: list[str],
    command: str,
) -> list[str]:
    """Adjust style.zIndex for selection. Returns changed ids."""
    cmd = str(command or "").strip()
    id_set = {str(i).strip() for i in block_ids if str(i).strip()}
    selected = [
        b
        for b in blocks
        if isinstance(b, dict) and str(b.get("id") or "").strip() in id_set
    ]
    if not selected:
        return []

    all_z = [_style_z(b) for b in blocks if isinstance(b, dict)]
    max_z = max(all_z) if all_z else 0
    min_z = min(all_z) if all_z else 0
    changed: list[str] = []

    if cmd == "bring-to-front":
        next_z = max_z + 1
        for block in selected:
            _set_z(block, next_z)
            next_z += 1
            changed.append(str(block.get("id") or ""))
    elif cmd == "send-to-back":
        next_z = min_z - len(selected)
        for block in selected:
            _set_z(block, next_z)
            next_z += 1
            changed.append(str(block.get("id") or ""))
    elif cmd == "bring-forward":
        for block in selected:
            _set_z(block, _style_z(block) + 1)
            changed.append(str(block.get("id") or ""))
    elif cmd == "send-backward":
        for block in selected:
            _set_z(block, _style_z(block) - 1)
            changed.append(str(block.get("id") or ""))
    else:
        raise ValueError(f"Comando de z-order inválido: {command}")

    return [c for c in changed if c]


def duplicate_blocks(
    blocks: list[dict[str, Any]],
    block_ids: list[str],
    *,
    offset_x: float = 2.0,
    offset_y: float = 2.0,
    new_id_fn,
) -> list[dict[str, Any]]:
    """Return new block dicts (not yet appended) cloned from selection."""
    id_set = {str(i).strip() for i in block_ids if str(i).strip()}
    clones: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        bid = str(block.get("id") or "").strip()
        if bid not in id_set:
            continue
        clone = copy_block_without_resolved(block)
        clone["id"] = new_id_fn()
        fr = _frame_of(clone)
        if fr is not None:
            _set_frame_xy(clone, x=fr["x"] + offset_x, y=fr["y"] + offset_y)
        clones.append(clone)
    return clones


def copy_block_without_resolved(block: dict[str, Any]) -> dict[str, Any]:
    import copy

    clone = copy.deepcopy(block)
    clone.pop("resolved", None)
    # Drop enrich-only paint stamps; reload will re-materialize.
    for key in (
        "displayText",
        "displayRuns",
        "displayValue",
        "displayLabel",
        "displayRows",
        "displaySeries",
        "kpiPresentation",
        "gaugeModel",
        "efficiencyPinPresentation",
        "yAxisTicks",
        "serverDisplayApplied",
        "serverProjectionApplied",
        "resolvedRouteLabel",
        "fieldLabelsEffective",
    ):
        clone.pop(key, None)
    return clone
