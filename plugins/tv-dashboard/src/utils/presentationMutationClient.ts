/**
 * Editor bridge → PresentationMutation commit (TV-DASHBOARD-PRESENTATION-001).
 *
 * Local gesture may preview; durable geometry/style/create must ack via API and
 * replace the editor model with the canonical nativeConfig from the backend.
 */

import { parseComunicadoConfig, type ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import {
  applyPresentationMutations,
  type PresentationMutationOp,
} from "../api/tvDashboardApi";

export async function commitPresentationOps(args: {
  playlistId: string;
  slideId: string;
  ops: PresentationMutationOp[];
}): Promise<ComunicadoConfig | null> {
  const { playlistId, slideId, ops } = args;
  if (!playlistId || !slideId || ops.length === 0) return null;
  const result = await applyPresentationMutations(playlistId, slideId, ops);
  const raw = result.nativeConfig;
  if (!raw || typeof raw !== "object") return null;
  return parseComunicadoConfig(raw);
}

/** Fire create_block and return canonical config (or null on skip/failure). */
export async function commitCreateBlock(args: {
  playlistId: string;
  slideId: string;
  type: string;
  blockId?: string;
  chartType?: string;
  shape?: string;
  iconName?: string;
  content?: string;
  frame?: Record<string, number>;
  style?: Record<string, unknown>;
}): Promise<ComunicadoConfig | null> {
  const op: PresentationMutationOp = {
    op: "create_block",
    type: args.type,
  };
  if (args.blockId) op.blockId = args.blockId;
  if (args.chartType) op.chartType = args.chartType;
  if (args.shape) op.shape = args.shape;
  if (args.iconName) op.iconName = args.iconName;
  if (args.content) op.content = args.content;
  if (args.frame) op.frame = args.frame;
  if (args.style) op.style = args.style;
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [op],
  });
}

export async function commitAlignBlocks(args: {
  playlistId: string;
  slideId: string;
  blockIds: string[];
  command: string;
}): Promise<ComunicadoConfig | null> {
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [
      {
        op: "align_blocks",
        blockIds: args.blockIds,
        command: args.command,
      },
    ],
  });
}

export async function commitReorderBlockZ(args: {
  playlistId: string;
  slideId: string;
  blockIds: string[];
  command: "bring-to-front" | "send-to-back" | "bring-forward" | "send-backward";
}): Promise<ComunicadoConfig | null> {
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [
      {
        op: "reorder_block_z",
        blockIds: args.blockIds,
        command: args.command,
      },
    ],
  });
}

export async function commitDuplicateBlocks(args: {
  playlistId: string;
  slideId: string;
  blockIds: string[];
  offsetX?: number;
  offsetY?: number;
}): Promise<ComunicadoConfig | null> {
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [
      {
        op: "duplicate_blocks",
        blockIds: args.blockIds,
        ...(args.offsetX != null ? { offsetX: args.offsetX } : {}),
        ...(args.offsetY != null ? { offsetY: args.offsetY } : {}),
      },
    ],
  });
}

export async function commitUpsertBlocks(args: {
  playlistId: string;
  slideId: string;
  blocks: Record<string, unknown>[];
}): Promise<ComunicadoConfig | null> {
  if (args.blocks.length === 0) return null;
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: args.blocks.map((block) => ({
      op: "upsert_block",
      block,
      createIfMissing: true,
    })),
  });
}
