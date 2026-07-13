import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import { isPointShapeKind } from "@delpi/tv-dashboard-presentation";
import { clampFrameForBlock } from "@delpi/tv-dashboard-presentation";

/** Fallback legado quando não há tamanho de design (testes / chamadas antigas). */
export const SNAP_GRID_PERCENT = 5;
export const SNAP_CENTER_THRESHOLD = 1.5;

export type SnapGridAxes = {
  /** Passo em % no eixo X (largura do palco). */
  xPercent: number;
  /** Passo em % no eixo Y (altura do palco). */
  yPercent: number;
};

export function snapToGrid(value: number, grid = SNAP_GRID_PERCENT): number {
  if (!(grid > 0)) return value;
  return Math.round(value / grid) * grid;
}

function snapCenterEdge(value: number, size: number): number {
  const center = value + size / 2;
  if (Math.abs(center - 50) <= SNAP_CENTER_THRESHOLD) {
    return 50 - size / 2;
  }
  return value;
}

function resolveAxes(grid?: SnapGridAxes): SnapGridAxes {
  if (grid && grid.xPercent > 0 && grid.yPercent > 0) return grid;
  return { xPercent: SNAP_GRID_PERCENT, yPercent: SNAP_GRID_PERCENT };
}

/** Aplica grade e guias ao centro do palco (após drag/resize). */
export function snapComunicadoFrame(
  block: ComunicadoBlock,
  frame: ComunicadoFrame,
  mode: "move" | "resize",
  grid?: SnapGridAxes,
): ComunicadoFrame {
  const axes = resolveAxes(grid);
  let next = { ...frame };

  if (block.type === "shape" && isPointShapeKind(block.shape)) {
    let x = snapToGrid(next.x, axes.xPercent);
    let y = snapToGrid(next.y, axes.yPercent);
    if (Math.abs(x - 50) <= SNAP_CENTER_THRESHOLD) x = 50;
    if (Math.abs(y - 50) <= SNAP_CENTER_THRESHOLD) y = 50;
    return clampFrameForBlock(block, { x, y, w: 0, h: 0 });
  }

  if (mode === "move") {
    next.x = snapToGrid(next.x, axes.xPercent);
    next.y = snapToGrid(next.y, axes.yPercent);
    next.x = snapCenterEdge(next.x, next.w);
    next.y = snapCenterEdge(next.y, next.h);
  } else {
    next.w = Math.max(axes.xPercent, snapToGrid(next.w, axes.xPercent));
    next.h = Math.max(axes.yPercent, snapToGrid(next.h, axes.yPercent));
    next.x = snapToGrid(next.x, axes.xPercent);
    next.y = snapToGrid(next.y, axes.yPercent);
  }

  return clampFrameForBlock(block, next);
}
