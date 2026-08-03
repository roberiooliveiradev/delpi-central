import {
  isDataTransformV1,
  normalizeDataTransform,
  type ComunicadoConfig,
  type ComunicadoDataSourceBlock,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";

import {
  requestDataPreviewBlock,
  serializeNativeConfigForPreview,
  stripBlockResolvedForPreview,
} from "./dataPreviewRequest";

export type ServerTransformTable = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
};

/**
 * Prévia tabular pós-Query — sempre via tv-dashboard-api (nunca engine no browser).
 * `stepsThrough` = etapas até o índice selecionado (vazio = só Fonte).
 */
export async function previewTransformTableOnServer(options: {
  block: ComunicadoDataSourceBlock;
  config: ComunicadoConfig;
  playlistId: string;
  playlistDefaults?: Record<string, unknown> | null;
  stepsThrough: DataTransformStep[];
  forceRefresh?: boolean;
}): Promise<ServerTransformTable> {
  const transform = normalizeDataTransform({ steps: options.stepsThrough });
  const payload: Record<string, unknown> = {
    ...stripBlockResolvedForPreview(options.block),
  };
  if (isDataTransformV1(transform) && transform.steps.length) {
    payload.dataTransform = transform;
  } else {
    delete payload.dataTransform;
  }

  const response = await requestDataPreviewBlock({
    block: payload,
    nativeConfig: serializeNativeConfigForPreview(options.config),
    playlistId: options.playlistId,
    playlistDefaults: options.playlistDefaults,
    forceRefresh: Boolean(options.forceRefresh),
  });

  const resolved = (response.block as { resolved?: Record<string, unknown> } | undefined)?.resolved;
  const table = resolved?.table as
    | {
        columns?: Array<{ key?: string; label?: string }>;
        rows?: Array<Record<string, unknown>>;
      }
    | undefined;

  const columns = (table?.columns ?? [])
    .map((col) => String(col.key || "").trim())
    .filter(Boolean);
  const rows = Array.isArray(table?.rows) ? table.rows.map((row) => ({ ...row })) : [];
  return { columns, rows };
}
