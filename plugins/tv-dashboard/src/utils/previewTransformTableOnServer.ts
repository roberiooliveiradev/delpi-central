import {
  isDataTransformV1,
  normalizeDataTransform,
  serializeComunicadoConfig,
  type ComunicadoConfig,
  type ComunicadoDataSourceBlock,
  type DataTransformStep,
} from "@delpi/tv-dashboard-presentation";

import { previewDataBlockV2 } from "../api/tvDashboardApi";

export type ServerTransformTable = {
  columns: string[];
  rows: Array<Record<string, unknown>>;
};

function stripResolved(block: ComunicadoDataSourceBlock): Record<string, unknown> {
  const { resolved: _resolved, ...rest } = block;
  return rest as Record<string, unknown>;
}

/**
 * Prévia tabular pós-Query — sempre via tv-dashboard-api (nunca engine no browser).
 * `stepsThrough` = etapas até o índice selecionado (vazio = só Fonte).
 */
export async function previewTransformTableOnServer(options: {
  block: ComunicadoDataSourceBlock;
  config: ComunicadoConfig;
  playlistId: string;
  stepsThrough: DataTransformStep[];
  forceRefresh?: boolean;
}): Promise<ServerTransformTable> {
  const transform = normalizeDataTransform({ steps: options.stepsThrough });
  const payload: Record<string, unknown> = {
    ...stripResolved(options.block),
  };
  if (isDataTransformV1(transform) && transform.steps.length) {
    payload.dataTransform = transform;
  } else {
    delete payload.dataTransform;
  }

  const response = await previewDataBlockV2({
    block: payload,
    nativeConfig: serializeComunicadoConfig(options.config),
    playlistId: options.playlistId,
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
