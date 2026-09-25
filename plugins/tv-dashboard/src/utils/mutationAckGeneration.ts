/**
 * PresentationMutation ack with generation guard (RIBBON-TEXT-002).
 *
 * Optimistic local preview is allowed; durable state comes from nativeConfig ack.
 * Stale responses (older generation) must not overwrite newer editor revisions.
 */

import type { ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import type { PresentationMutationOp } from "../api/tvDashboardApi";
import { commitPresentationOps, commitUpsertBlocks } from "./presentationMutationClient";

export type MutationAckApply = (canonical: ComunicadoConfig) => void;

export function createMutationGenerationGate() {
  let generation = 0;

  return {
    next(): number {
      generation += 1;
      return generation;
    },
    isCurrent(token: number): boolean {
      return token === generation;
    },
    current(): number {
      return generation;
    },
  };
}

export type MutationGenerationGate = ReturnType<typeof createMutationGenerationGate>;

/**
 * Upsert blocks and apply canonical ack when still current.
 * Returns applied canonical config, or null if skipped/stale/failed.
 */
export async function ackUpsertBlocksWithGeneration(args: {
  playlistId: string;
  slideId: string;
  blocks: Record<string, unknown>[];
  gate: MutationGenerationGate;
  applyAck: MutationAckApply;
}): Promise<ComunicadoConfig | null> {
  const { playlistId, slideId, blocks, gate, applyAck } = args;
  if (!playlistId || !slideId || blocks.length === 0) return null;
  const token = gate.next();
  try {
    const canonical = await commitUpsertBlocks({ playlistId, slideId, blocks });
    if (!canonical || !gate.isCurrent(token)) return null;
    applyAck(canonical);
    return canonical;
  } catch {
    return null;
  }
}

/**
 * Commit typed ops and apply ack when still current.
 */
export async function commitOpsAndApplyAck(args: {
  playlistId: string;
  slideId: string;
  ops: PresentationMutationOp[];
  gate: MutationGenerationGate;
  applyAck: MutationAckApply;
  /** Local preview applied before the network round-trip. */
  optimistic?: () => void;
}): Promise<ComunicadoConfig | null> {
  const { playlistId, slideId, ops, gate, applyAck, optimistic } = args;
  if (!playlistId || !slideId || ops.length === 0) return null;
  const token = gate.next();
  optimistic?.();
  try {
    const canonical = await commitPresentationOps({ playlistId, slideId, ops });
    if (!canonical) {
      return null;
    }
    if (!gate.isCurrent(token)) return null;
    applyAck(canonical);
    return canonical;
  } catch {
    return null;
  }
}
