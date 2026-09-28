import {
  serializeComunicadoConfig,
  type ComunicadoConfig,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2, previewDataModelV2 } from "../api/tvDashboardApi";

/**
 * Contrato único do POST `/data/preview-block` no editor.
 * Todo refetch (palco, catálogo, Query, transform) passa por aqui —
 * inclui `playlistDefaults` live para não depender só do valor no banco.
 */
export type DataPreviewBlockRequestInput = {
  block: Record<string, unknown>;
  nativeConfig: Record<string, unknown>;
  playlistId?: string;
  /** dataDefaults live da programação (estado do editor). */
  playlistDefaults?: Record<string, unknown> | null;
  forceRefresh?: boolean;
  targetStepName?: string | null;
  previewOptions?: {
    maxRows?: number;
    includeColumnProfile?: boolean;
    deadlineMs?: number;
  };
  signal?: AbortSignal;
};

/** Remove `resolved` antes de mandar o bloco ao preview (evita eco de cache no body). */
export function stripBlockResolvedForPreview(
  block: Record<string, unknown> | { resolved?: unknown },
): Record<string, unknown> {
  if (!block || typeof block !== "object") return {};
  const { resolved: _resolved, ...rest } = block as Record<string, unknown> & {
    resolved?: unknown;
  };
  return rest;
}

export function serializeNativeConfigForPreview(
  config: ComunicadoConfig,
): Record<string, unknown> {
  return serializeComunicadoConfig(config) as Record<string, unknown>;
}

/** Monta o body canônico (sem signal) para `previewDataBlockV2`. */
export function buildDataPreviewBlockRequest(
  input: DataPreviewBlockRequestInput,
): {
  block: Record<string, unknown>;
  nativeConfig: Record<string, unknown>;
  playlistId?: string;
  playlistDefaults?: Record<string, unknown>;
  forceRefresh?: boolean;
  targetStepName?: string;
  previewOptions?: DataPreviewBlockRequestInput["previewOptions"];
  signal?: AbortSignal;
} {
  const defaults =
    input.playlistDefaults && typeof input.playlistDefaults === "object"
      ? input.playlistDefaults
      : undefined;
  return {
    block: input.block,
    nativeConfig: input.nativeConfig,
    ...(input.playlistId ? { playlistId: input.playlistId } : {}),
    ...(defaults ? { playlistDefaults: defaults } : {}),
    forceRefresh: Boolean(input.forceRefresh),
    ...(input.targetStepName != null && input.targetStepName !== ""
      ? { targetStepName: input.targetStepName }
      : {}),
    ...(input.previewOptions ? { previewOptions: input.previewOptions } : {}),
    ...(input.signal ? { signal: input.signal } : {}),
  };
}

/** Único caminho HTTP de preview-block a partir do MFE. */
export async function requestDataPreviewBlock(input: DataPreviewBlockRequestInput) {
  return previewDataBlockV2(buildDataPreviewBlockRequest(input));
}

export type DataPreviewModelRequestInput = {
  /** Modelo persistido no config (enviado serializado — sem artefatos de runtime). */
  model: TvDataModel;
  nativeConfig: Record<string, unknown>;
  playlistId?: string;
  playlistDefaults?: Record<string, unknown> | null;
  forceRefresh?: boolean;
  signal?: AbortSignal;
};

/** Serializa o modelo pelo whitelist persistido — nunca artefatos de runtime. */
export function serializeDataModelForPreview(
  model: TvDataModel,
): Record<string, unknown> {
  return {
    id: model.id,
    primaryInputId: model.primaryInputId,
    inputs: model.inputs.map((input) => ({
      id: input.id,
      operationId: input.operationId,
      ...(input.label ? { label: input.label } : {}),
      ...(input.queryName ? { queryName: input.queryName } : {}),
      ...(input.params ? { params: { ...input.params } } : {}),
      ...(input.transform !== undefined && input.transform !== null
        ? { transform: input.transform }
        : {}),
    })),
    ...(model.label ? { label: model.label } : {}),
    ...(model.transform !== undefined && model.transform !== null
      ? { transform: model.transform }
      : {}),
    ...(model.fieldLabels ? { fieldLabels: { ...model.fieldLabels } } : {}),
  };
}

/** Único caminho HTTP de preview-model a partir do MFE (`/data/preview-model`). */
export async function requestDataPreviewModel(input: DataPreviewModelRequestInput) {
  const defaults =
    input.playlistDefaults && typeof input.playlistDefaults === "object"
      ? input.playlistDefaults
      : undefined;
  return previewDataModelV2({
    model: serializeDataModelForPreview(input.model),
    modelId: input.model.id,
    nativeConfig: input.nativeConfig,
    ...(input.playlistId ? { playlistId: input.playlistId } : {}),
    ...(defaults ? { playlistDefaults: defaults } : {}),
    forceRefresh: Boolean(input.forceRefresh),
    ...(input.signal ? { signal: input.signal } : {}),
  });
}
