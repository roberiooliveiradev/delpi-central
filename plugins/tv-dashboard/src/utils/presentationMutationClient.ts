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
import { isParamExpressionValue } from "./paramExpressions";

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

export async function commitPatchNativeConfig(args: {
  playlistId: string;
  slideId: string;
  patch: Record<string, unknown>;
}): Promise<ComunicadoConfig | null> {
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [{ op: "patch_native_config", patch: args.patch }],
  });
}

/** Upsert DataModel persisted in `nativeConfig.dataModels[]` (DM1/DM3). */
export async function commitUpsertDataModel(args: {
  playlistId: string;
  slideId: string;
  model: Record<string, unknown>;
}): Promise<ComunicadoConfig | null> {
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [{ op: "upsert_data_model", model: args.model }],
  });
}

/** Delete DataModel — backend rejects `data_model.in_use` with consumer details. */
export async function commitDeleteDataModel(args: {
  playlistId: string;
  slideId: string;
  modelId: string;
}): Promise<ComunicadoConfig | null> {
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops: [{ op: "delete_data_model", modelId: args.modelId }],
  });
}

/**
 * Divide `dataBinding.params` do bloco: ExpressionSpec não entra em
 * `upsert_block` (schema scalar-only do contrato) — vai por
 * `patch_data_source_params`, op governada que aceita ExpressionSpec em `set`.
 * Retorna `{block, expressionSet}` — `expressionSet` vazio quando nada a patchear.
 * Exportado para testes do contrato de split.
 */
export function splitBlockForAck(block: Record<string, unknown>): {
  block: Record<string, unknown>;
  expressionSet: Record<string, unknown>;
} {
  const binding =
    block.dataBinding && typeof block.dataBinding === "object" && !Array.isArray(block.dataBinding)
      ? (block.dataBinding as Record<string, unknown>)
      : null;
  const params =
    binding?.params && typeof binding.params === "object" && !Array.isArray(binding.params)
      ? (binding.params as Record<string, unknown>)
      : null;
  if (!binding || !params) return { block, expressionSet: {} };

  const expressionSet: Record<string, unknown> = {};
  const scalarParams: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(params)) {
    if (isParamExpressionValue(value)) expressionSet[key] = value;
    else scalarParams[key] = value;
  }
  if (Object.keys(expressionSet).length === 0) {
    return { block, expressionSet: {} };
  }
  return {
    block: {
      ...block,
      dataBinding: { ...binding, params: scalarParams },
    },
    expressionSet,
  };
}

export async function commitUpsertBlocks(args: {
  playlistId: string;
  slideId: string;
  blocks: Record<string, unknown>[];
}): Promise<ComunicadoConfig | null> {
  if (args.blocks.length === 0) return null;
  const ops: PresentationMutationOp[] = [];
  for (const raw of args.blocks) {
    const { block, expressionSet } = splitBlockForAck(raw);
    ops.push({ op: "upsert_block", block, createIfMissing: true });
    if (Object.keys(expressionSet).length > 0 && typeof block.id === "string") {
      ops.push({
        op: "patch_data_source_params",
        blockId: block.id,
        set: expressionSet,
      });
    }
  }
  return commitPresentationOps({
    playlistId: args.playlistId,
    slideId: args.slideId,
    ops,
  });
}
