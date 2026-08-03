import {
  isFetchableDataBlockType,
  parseComunicadoConfig,
  type ComunicadoBlock,
} from "@delpi/tv-dashboard-presentation";
import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  visibleParamSchema,
  type DataParamSchema,
} from "../components/DataParamFields";
import {
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
} from "./dateRangePresets";

export type SlideNativeConfigLike = {
  nativeConfig?: Record<string, unknown> | null;
};

/**
 * Params de paginação/cursor — por fonte no inspector; não entram em filtros
 * agregados (programação / slide).
 */
export const AGGREGATE_EXCLUDED_PARAM_KEYS = new Set([
  "page",
  "page_size",
  "pageSize",
  "offset",
  "cursor",
  "skip",
  "take",
]);

function isMeaningfulDefault(value: unknown): boolean {
  if (value === undefined || value === null) return false;
  if (typeof value === "string") return value.trim().length > 0;
  return true;
}

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

function stripAggregateExcludedKeys(schema: DataParamSchema): DataParamSchema {
  return Object.fromEntries(
    Object.entries(schema).filter(([key]) => !AGGREGATE_EXCLUDED_PARAM_KEYS.has(key)),
  );
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
    const visible = visibleParamSchema(
      route.paramSchema as DataParamSchema,
      route.fixedQueryParams as Record<string, unknown> | undefined,
    );
    for (const [key, field] of Object.entries(visible)) {
      if (!merged[key]) merged[key] = field;
    }
  }
  return stripAggregateExcludedKeys(merged);
}

/**
 * Remove do schema do slide as chaves já definidas em dataDefaults (programação),
 * para não repetir o mesmo campo nas duas camadas da UI.
 * Preset de período também cobre periodDays e o par de datas.
 */
export function omitSchemaKeysCoveredByDefaults(
  schema: DataParamSchema,
  defaults: Record<string, unknown> | null | undefined,
): DataParamSchema {
  if (!defaults || typeof defaults !== "object") return schema;

  const covered = new Set<string>();
  for (const [key, value] of Object.entries(defaults)) {
    if (isMeaningfulDefault(value)) covered.add(key);
  }
  if (covered.size === 0) return schema;

  if (covered.has(DATE_RANGE_PRESET_PARAM)) {
    covered.add(PERIOD_DAYS_PARAM);
    const pair = findDateRangeKeys(Object.keys(schema));
    if (pair) {
      covered.add(pair.startKey);
      covered.add(pair.endKey);
    }
  }

  return Object.fromEntries(Object.entries(schema).filter(([key]) => !covered.has(key)));
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
  playlistDefaults?: Record<string, unknown> | null,
): DataParamSchema {
  const merged = mergeRouteParamSchemas(routes, collectOperationIdsFromNativeConfig(nativeConfig));
  return omitSchemaKeysCoveredByDefaults(merged, playlistDefaults);
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
