import {
  isFetchableDataBlockType,
  parseComunicadoConfig,
  type ComunicadoBlock,
  type ParamExpressionSpec,
  type TvDataModel,
} from "@delpi/tv-dashboard-presentation";
import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  visibleParamSchema,
  type DataParamSchema,
  type DataParamSchemaField,
} from "./dataParamSchema";
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

/**
 * operationIds de todos os alvos de dados do slide: blocos fetchable
 * (data_source / data_*) + `dataModels[].inputs[].operationId`. Canal
 * canônico de descoberta de schema — playlist, slide, ribbon e inputs
 * de filtro consomem o mesmo conjunto (paridade legacy ↔ DataModel).
 */
export function collectDataOperationIds(config: {
  blocks?: ComunicadoBlock[] | null;
  dataModels?: readonly TvDataModel[] | null;
}): string[] {
  const ids = new Set(collectFetchableOperationIds(config.blocks ?? []));
  for (const model of config.dataModels ?? []) {
    for (const input of model.inputs ?? []) {
      const operationId = String(input.operationId ?? "").trim();
      if (operationId) ids.add(operationId);
    }
  }
  return [...ids];
}

export function collectOperationIdsFromNativeConfig(
  nativeConfig: Record<string, unknown> | null | undefined,
): string[] {
  if (!nativeConfig || typeof nativeConfig !== "object") return [];
  return collectDataOperationIds(parseComunicadoConfig(nativeConfig));
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

/** Chave de parâmetro cujo schema diverge entre rotas do mesmo agregado. */
export type RouteParamSchemaConflict = {
  key: string;
  operationIds: string[];
};

function sameStringSet(
  a: ReadonlyArray<string | number | boolean> | undefined,
  b: ReadonlyArray<string | number | boolean> | undefined,
): boolean {
  if (!a?.length || !b?.length) return true;
  const bSet = new Set(b.map(String));
  return a.some((item) => bSet.has(String(item)));
}

/**
 * Duas definições da mesma chave são compatíveis para merge agregado quando
 * têm o mesmo type/format e enums com interseção não vazia. Conflito real
 * (ex.: `period` string vs integer, enums disjuntos) NÃO entra no schema
 * agregado — campo ambíguo ficaria sem semântica definida.
 */
export function paramSchemaFieldsCompatible(
  a: DataParamSchemaField,
  b: DataParamSchemaField,
): boolean {
  if ((a.type ?? "string") !== (b.type ?? "string")) return false;
  const formatA = String(a.format ?? "").toLowerCase();
  const formatB = String(b.format ?? "").toLowerCase();
  if (formatA && formatB && formatA !== formatB) return false;
  return sameStringSet(a.enum, b.enum);
}

/**
 * Une paramSchema das rotas. Compatíveis → merge (enum = interseção, domínio
 * seguro para todas as rotas). Incompatíveis → chave excluída do agregado e
 * listada em `conflicts` para feedback; edição por fonte/input segue íntegra.
 */
export function mergeRouteParamSchemasDetailed(
  routes: TvDataRouteCatalogItem[],
  operationIds: Iterable<string>,
): { schema: DataParamSchema; conflicts: RouteParamSchemaConflict[] } {
  const byId = new Map(routes.map((route) => [route.operationId, route] as const));
  const merged: DataParamSchema = {};
  const declaringOpsByKey = new Map<string, Set<string>>();
  const conflicts = new Map<string, RouteParamSchemaConflict>();
  for (const operationId of operationIds) {
    const route = byId.get(operationId);
    if (!route?.paramSchema) continue;
    const visible = visibleParamSchema(
      route.paramSchema as DataParamSchema,
      route.fixedQueryParams as Record<string, unknown> | undefined,
    );
    for (const [key, field] of Object.entries(visible)) {
      const declaringOps = declaringOpsByKey.get(key) ?? new Set<string>();
      declaringOpsByKey.set(key, declaringOps);
      declaringOps.add(operationId);
      if (conflicts.has(key)) {
        // Chave já excluída por incompatibilidade — segue fora do agregado.
        conflicts.set(key, { key, operationIds: [...declaringOps] });
        continue;
      }
      const current = merged[key];
      if (!current) {
        merged[key] = field;
        continue;
      }
      if (paramSchemaFieldsCompatible(current, field)) {
        // Enum agregado = interseção (valor precisa ser válido em todas as
        // rotas que declaram o domínio); demais metadados vêm do primeiro.
        if (current.enum?.length && field.enum?.length) {
          const allowed = new Set(field.enum.map(String));
          current.enum = current.enum.filter((item) => allowed.has(String(item)));
        }
        continue;
      }
      delete merged[key];
      conflicts.set(key, { key, operationIds: [...declaringOps] });
    }
  }
  return {
    schema: stripAggregateExcludedKeys(merged),
    conflicts: [...conflicts.values()],
  };
}

/** Une paramSchema das rotas (ver `mergeRouteParamSchemasDetailed`). */
export function mergeRouteParamSchemas(
  routes: TvDataRouteCatalogItem[],
  operationIds: Iterable<string>,
): DataParamSchema {
  return mergeRouteParamSchemasDetailed(routes, operationIds).schema;
}

/**
 * Remove chaves do schema cobertas por um mapa de defaults (uso pontual / legado).
 * Tela e Programação **não** usam isto na UI — campos podem repetir; a precedência
 * no merge é input > dados > tela > programação.
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

/** Schema de filtros da tela = união das fontes do slide (sem omitir Programação). */
export function collectSlideDataParamSchema(
  nativeConfig: Record<string, unknown> | null | undefined,
  routes: TvDataRouteCatalogItem[],
): DataParamSchema {
  return mergeRouteParamSchemas(routes, collectOperationIdsFromNativeConfig(nativeConfig));
}

/** Normaliza dataDefaults / dataFilters para o editor de params. */
export function asDataFilterValues(
  raw: Record<string, unknown> | null | undefined,
): Record<string, string | number | boolean | null | ParamExpressionSpec> {
  if (!raw || typeof raw !== "object") return {};
  const next: Record<string, string | number | boolean | null | ParamExpressionSpec> = {};
  for (const [key, value] of Object.entries(raw)) {
    if (value === undefined) continue;
    if (value === null || typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
      next[key] = value;
    } else if (typeof value === "object" && !Array.isArray(value)) {
      // ExpressionSpec (objeto) persiste intacto — backend é autoridade do contrato.
      next[key] = value as ParamExpressionSpec;
    } else {
      next[key] = String(value);
    }
  }
  return next;
}
