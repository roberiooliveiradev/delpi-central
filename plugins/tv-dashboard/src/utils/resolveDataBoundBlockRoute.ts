import type { ComunicadoBlock } from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";

/**
 * operationId da rota ligada a qualquer bloco que use dados:
 * fonte/legado (`dataBinding`) ou visual/texto/grade (`dataSourceId` → fonte).
 */
export function resolveOperationIdForDataBoundBlock(
  block: ComunicadoBlock | null | undefined,
  blocks: ComunicadoBlock[],
): string | null {
  if (!block) return null;
  if ("dataBinding" in block) {
    const direct = String(block.dataBinding?.operationId ?? "").trim();
    if (direct) return direct;
  }
  const sourceId =
    "dataSourceId" in block && typeof block.dataSourceId === "string"
      ? block.dataSourceId.trim()
      : "";
  if (!sourceId) return null;
  const source = blocks.find((item) => item.id === sourceId);
  if (!source || !("dataBinding" in source)) return null;
  const fromSource = String(source.dataBinding?.operationId ?? "").trim();
  return fromSource || null;
}

/** Rota do catálogo vivo para o bloco (label / valueFields). */
export function resolveRouteForDataBoundBlock(
  block: ComunicadoBlock | null | undefined,
  blocks: ComunicadoBlock[],
  routes: readonly TvDataRouteCatalogItem[],
): TvDataRouteCatalogItem | null {
  const operationId = resolveOperationIdForDataBoundBlock(block, blocks);
  if (!operationId) return null;
  return routes.find((route) => route.operationId === operationId) ?? null;
}
