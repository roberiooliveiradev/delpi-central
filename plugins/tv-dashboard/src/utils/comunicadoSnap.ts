import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import { isPointShapeKind } from "@delpi/tv-dashboard-presentation";
import { clampFrameForBlock } from "@delpi/tv-dashboard-presentation";

export const SNAP_GRID_PERCENT = 5;
export const SNAP_CENTER_THRESHOLD = 1.5;

export function snapToGrid(value: number, grid = SNAP_GRID_PERCENT): number {
  return Math.round(value / grid) * grid;
}

function snapCenterEdge(value: number, size: number): number {
  const center = value + size / 2;
  if (Math.abs(center - 50) <= SNAP_CENTER_THRESHOLD) {
    return 50 - size / 2;
  }
  return value;
}

/** Aplica grid 5% e guias ao centro do palco (após drag/resize). */
export function snapComunicadoFrame(
  block: ComunicadoBlock,
  frame: ComunicadoFrame,
  mode: "move" | "resize",
): ComunicadoFrame {
  let next = { ...frame };

  if (block.type === "shape" && isPointShapeKind(block.shape)) {
    let x = snapToGrid(next.x);
    let y = snapToGrid(next.y);
    if (Math.abs(x - 50) <= SNAP_CENTER_THRESHOLD) x = 50;
    if (Math.abs(y - 50) <= SNAP_CENTER_THRESHOLD) y = 50;
    return clampFrameForBlock(block, { x, y, w: 0, h: 0 });
  }

  if (mode === "move") {
    next.x = snapToGrid(next.x);
    next.y = snapToGrid(next.y);
    next.x = snapCenterEdge(next.x, next.w);
    next.y = snapCenterEdge(next.y, next.h);
  } else {
    next.w = Math.max(SNAP_GRID_PERCENT, snapToGrid(next.w));
    next.h = Math.max(SNAP_GRID_PERCENT, snapToGrid(next.h));
    next.x = snapToGrid(next.x);
    next.y = snapToGrid(next.y);
  }

  return clampFrameForBlock(block, next);
}
