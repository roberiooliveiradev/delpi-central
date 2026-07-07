import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import { clampFrame } from "@delpi/tv-dashboard-presentation";

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
export function snapComunicadoFrame(frame: ComunicadoFrame, mode: "move" | "resize"): ComunicadoFrame {
  let next = { ...frame };

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

  return clampFrame(next);
}
