import {
  bindingTargetKind,
  bindingTargetId,
  findDataModel,
  type ComunicadoBlock,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";

/**
 * operationId da rota ligada a qualquer bloco que use dados:
 * fonte/legado (`dataBinding`), visual/texto/grade (`dataSourceId` → fonte)
 * ou DataModel (`modelId` → `primaryInputId` do modelo).
 */
export function resolveOperationIdForDataBoundBlock(
  block: ComunicadoBlock | null | undefined,
  blocks: ComunicadoBlock[],
  dataModels?: readonly TvDataModel[] | null,
): string | null {
  if (!block) return null;
  if ("dataBinding" in block) {
    const direct = String(block.dataBinding?.operationId ?? "").trim();
    if (direct) return direct;
  }
  if (bindingTargetKind(block) === "model") {
    const model = findDataModel(
      { dataModels: [...(dataModels ?? [])] },
      bindingTargetId(block),
    );
    const inputId = model?.primaryInputId?.trim() ?? "";
    const operationId = inputId
      ? (model?.inputs.find((input) => input.id === inputId)?.operationId?.trim() ?? "")
      : (model?.inputs[0]?.operationId?.trim() ?? "");
    return operationId || null;
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
  dataModels?: readonly TvDataModel[] | null,
): TvDataRouteCatalogItem | null {
  const operationId = resolveOperationIdForDataBoundBlock(block, blocks, dataModels);
  if (!operationId) return null;
  return routes.find((route) => route.operationId === operationId) ?? null;
}
