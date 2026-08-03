import {
  isFetchableDataBlockType,
  parseComunicadoConfig,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import type { DataParamSchema } from "../components/DataParamFields";

export type SlideNativeConfigLike = {
  nativeConfig?: Record<string, unknown> | null;
};

/** operationIds de blocos que disparam fetch (data_source / data_*). */
export function collectFetchableOperationIds(blocks: ComunicadoBlock[]): string[] {
  const ids = new Set<string>();
  for (const block of blocks) {
    if (!isFetchableDataBlockType(block.type)) continue;
    if (!("dataBinding" in block) || !block.dataBinding?.operationId) continue;
    const operationId = String(block.dataBinding.operationId).trim();
    if (operationId) ids.add(operationId);
  }
  return [...ids];
}

export function collectOperationIdsFromNativeConfig(
  nativeConfig: Record<string, unknown> | null | undefined,
): string[] {
  if (!nativeConfig || typeof nativeConfig !== "object") return [];
  return collectFetchableOperationIds(parseComunicadoConfig(nativeConfig).blocks ?? []);
}

/** União de operationIds de todas as telas da programação. */
export function collectPlaylistOperationIds(slides: SlideNativeConfigLike[]): string[] {
  const ids = new Set<string>();
  for (const slide of slides) {
    for (const operationId of collectOperationIdsFromNativeConfig(slide.nativeConfig)) {
      ids.add(operationId);
    }
  }
  return [...ids];
}

/** Une paramSchema das rotas; a primeira definição de cada chave prevalece. */
export function mergeRouteParamSchemas(
  routes: TvDataRouteCatalogItem[],
  operationIds: Iterable<string>,
): DataParamSchema {
  const byId = new Map(routes.map((route) => [route.operationId, route] as const));
  const merged: DataParamSchema = {};
  for (const operationId of operationIds) {
    const route = byId.get(operationId);
    if (!route?.paramSchema) continue;
    for (const [key, field] of Object.entries(route.paramSchema)) {
      if (!merged[key]) merged[key] = field as DataParamSchema[string];
    }
  }
  return merged;
}

export function collectPlaylistDataParamSchema(
  slides: SlideNativeConfigLike[],
  routes: TvDataRouteCatalogItem[],
): DataParamSchema {
  return mergeRouteParamSchemas(routes, collectPlaylistOperationIds(slides));
}

export function collectSlideDataParamSchema(
  nativeConfig: Record<string, unknown> | null | undefined,
  routes: TvDataRouteCatalogItem[],
): DataParamSchema {
  return mergeRouteParamSchemas(routes, collectOperationIdsFromNativeConfig(nativeConfig));
}

/** Normaliza dataDefaults / dataFilters para o editor de params. */
export function asDataFilterValues(
  raw: Record<string, unknown> | null | undefined,
): Record<string, string | number | boolean | null> {
  if (!raw || typeof raw !== "object") return {};
  const next: Record<string, string | number | boolean | null> = {};
  for (const [key, value] of Object.entries(raw)) {
    if (value === undefined) continue;
    if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      next[key] = value;
    } else {
      next[key] = String(value);
    }
  }
  return next;
}
