import { serializeComunicadoConfig, type ComunicadoConfig } from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2 } from "../api/tvDashboardApi";

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
