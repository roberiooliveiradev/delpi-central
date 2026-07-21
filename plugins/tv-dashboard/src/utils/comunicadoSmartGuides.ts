import type { ComunicadoFrame } from "@delpi/tv-dashboard-presentation";

/** Limiar em % do slide para encaixe em bordas/centros de outros blocos. */
export const SMART_GUIDE_THRESHOLD_PERCENT = 0.9;

export type SmartGuideLine = {
  orientation: "v" | "h";
  /** Posição em % do slide (x para vertical, y para horizontal). */
  position: number;
};

export type SmartGuideSnapResult = {
  frame: ComunicadoFrame;
  guides: SmartGuideLine[];
};

type AxisEdges = {
  start: number;
  end: number;
  center: number;
};

function axisEdgesX(frame: ComunicadoFrame): AxisEdges {
  return {
    start: frame.x,
    end: frame.x + frame.w,
    center: frame.x + frame.w / 2,
  };
}

function axisEdgesY(frame: ComunicadoFrame): AxisEdges {
  return {
    start: frame.y,
    end: frame.y + frame.h,
    center: frame.y + frame.h / 2,
  };
}

function peerTargets(edges: AxisEdges): number[] {
  return [edges.start, edges.end, edges.center];
}

type AxisSnap = {
  delta: number;
  guide: number;
};

function bestMoveDelta(
  moving: AxisEdges,
  peers: AxisEdges[],
  threshold: number,
): AxisSnap | null {
  let best: AxisSnap | null = null;
  for (const peer of peers) {
    for (const target of peerTargets(peer)) {
      for (const source of peerTargets(moving)) {
        const delta = target - source;
        const abs = Math.abs(delta);
        if (abs > threshold) continue;
        if (!best || abs < Math.abs(best.delta)) {
          best = { delta, guide: target };
        }
      }
    }
  }
  return best;
}

/**
 * Resize: escolhe o menor ajuste de uma única borda (início ou fim) no eixo.
 * Mantém a borda oposta fixa.
 */
function bestResizeSnap(
  moving: AxisEdges,
  peers: AxisEdges[],
  threshold: number,
): { edge: "start" | "end"; target: number; delta: number } | null {
  let best: { edge: "start" | "end"; target: number; delta: number } | null = null;
  for (const peer of peers) {
    for (const target of peerTargets(peer)) {
      for (const edge of ["start", "end"] as const) {
        const source = edge === "start" ? moving.start : moving.end;
        const delta = target - source;
        const abs = Math.abs(delta);
        if (abs > threshold) continue;
        if (!best || abs < Math.abs(best.delta)) {
          best = { edge, target, delta };
        }
      }
    }
  }
  return best;
}

function dedupeGuides(guides: SmartGuideLine[]): SmartGuideLine[] {
  const seen = new Set<string>();
  const out: SmartGuideLine[] = [];
  for (const guide of guides) {
    const key = `${guide.orientation}:${guide.position.toFixed(3)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(guide);
  }
  return out;
}

/**
 * Encaixa o quadro nas bordas e centros de outros blocos (smart guides).
 * Em `move`, desloca o bloco inteiro; em `resize`, ajusta uma borda por eixo.
 */
export function snapFrameToPeerBlocks(
  frame: ComunicadoFrame,
  peers: ComunicadoFrame[],
  mode: "move" | "resize",
  threshold = SMART_GUIDE_THRESHOLD_PERCENT,
): SmartGuideSnapResult {
  if (peers.length === 0 || !(threshold > 0)) {
    return { frame: { ...frame }, guides: [] };
  }

  const peerX = peers.map(axisEdgesX);
  const peerY = peers.map(axisEdgesY);
  const guides: SmartGuideLine[] = [];
  let next = { ...frame };

  if (mode === "move") {
    const snapX = bestMoveDelta(axisEdgesX(next), peerX, threshold);
    const snapY = bestMoveDelta(axisEdgesY(next), peerY, threshold);
    if (snapX) {
      next.x += snapX.delta;
      guides.push({ orientation: "v", position: snapX.guide });
    }
    if (snapY) {
      next.y += snapY.delta;
      guides.push({ orientation: "h", position: snapY.guide });
    }
    return { frame: next, guides: dedupeGuides(guides) };
  }

  const snapX = bestResizeSnap(axisEdgesX(next), peerX, threshold);
  if (snapX) {
    if (snapX.edge === "start") {
      const right = next.x + next.w;
      next.x = snapX.target;
      next.w = Math.max(0, right - next.x);
    } else {
      next.w = Math.max(0, snapX.target - next.x);
    }
    guides.push({ orientation: "v", position: snapX.target });
  }

  const snapY = bestResizeSnap(axisEdgesY(next), peerY, threshold);
  if (snapY) {
    if (snapY.edge === "start") {
      const bottom = next.y + next.h;
      next.y = snapY.target;
      next.h = Math.max(0, bottom - next.y);
    } else {
      next.h = Math.max(0, snapY.target - next.y);
    }
    guides.push({ orientation: "h", position: snapY.target });
  }

  return { frame: next, guides: dedupeGuides(guides) };
}

/** Frames de peers excluidos do conjunto arrastado. */
export function peerFramesForSmartGuides(
  blocks: ReadonlyArray<{ id: string; frame: ComunicadoFrame }>,
  excludeIds: ReadonlySet<string>,
): ComunicadoFrame[] {
  const frames: ComunicadoFrame[] = [];
  for (const block of blocks) {
    if (excludeIds.has(block.id)) continue;
    frames.push(block.frame);
  }
  return frames;
}
