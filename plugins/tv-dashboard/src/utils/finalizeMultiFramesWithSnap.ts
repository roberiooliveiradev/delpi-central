import type { ComunicadoBlock, ComunicadoFrame } from "@delpi/tv-dashboard-presentation";
import { clampFrameForBlock } from "@delpi/tv-dashboard-presentation";

import { applyMultiFrameDelta } from "./multiFrameTransform";
import { snapComunicadoFrame, type SnapGridAxes } from "./comunicadoSnap";

/**
 * No fim do gesto **unitário** (1 bloco): encaixa o frame e devolve.
 * Multi/grupo N>1: `useComunicadoEditorDrag` finaliza via `stageGroupGesture.resolveWorldFrames`
 * — não chamar este helper no resize de grupo (distorce com `applyMultiFrameDelta`).
 */
export function finalizeMultiFramesWithSnap(params: {
  blocks: ComunicadoBlock[];
  ids: string[];
  primaryId: string;
  /** Frames no início do gesto. */
  startFrames: ReadonlyMap<string, ComunicadoFrame>;
  /** Frames atuais (pós live / smart guides). */
  currentById: ReadonlyMap<string, ComunicadoFrame>;
  mode: "move" | "resize";
  snapToGrid: boolean;
  snapPercents?: SnapGridAxes;
}): Map<string, ComunicadoFrame> {
  const { blocks, ids, primaryId, startFrames, currentById, mode, snapToGrid, snapPercents } =
    params;
  const primaryBlock = blocks.find((block) => block.id === primaryId);
  const primaryCurrent = currentById.get(primaryId);
  if (!primaryBlock || !primaryCurrent) {
    const fallback = new Map<string, ComunicadoFrame>();
    for (const id of ids) {
      const frame = currentById.get(id);
      if (frame) fallback.set(id, { ...frame });
    }
    return fallback;
  }

  let primaryNext = primaryCurrent;
  if (snapToGrid) {
    primaryNext = snapComunicadoFrame(primaryBlock, primaryCurrent, mode, snapPercents);
  } else {
    primaryNext = clampFrameForBlock(primaryBlock, primaryCurrent);
  }

  if (ids.length === 1) {
    return new Map([[primaryId, primaryNext]]);
  }

  const starts = new Map<string, ComunicadoFrame>();
  for (const id of ids) {
    const start = startFrames.get(id) ?? currentById.get(id);
    if (start) starts.set(id, { ...start });
  }
  if (!starts.has(primaryId)) {
    starts.set(primaryId, { ...primaryCurrent });
  }

  return applyMultiFrameDelta(starts, primaryId, primaryNext);
}
