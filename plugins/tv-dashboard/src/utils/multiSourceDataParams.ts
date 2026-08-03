import {
  isDataSourceBlockType,
  isFetchableDataBlockType,
  type ComunicadoBlock,
  type ComunicadoDataBinding,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  visibleParamSchema,
  type DataParamSchema,
} from "../components/DataParamFields";
import { applyDataParamRawUpdates } from "./applyDataParamUpdates";
import {
  AGGREGATE_EXCLUDED_PARAM_KEYS,
  mergeRouteParamSchemas,
} from "./collectPlaylistDataParamSchema";
import {
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
  readDateRangeUpdateValues,
} from "./dateRangePresets";

export type MultiSourceBindingTarget = ComunicadoBlock & {
  dataBinding: ComunicadoDataBinding;
};

export function isMultiSourceBindingTarget(
  block: ComunicadoBlock | null | undefined,
): block is MultiSourceBindingTarget {
  if (!block) return false;
  if (!isDataSourceBlockType(block.type) && !isFetchableDataBlockType(block.type)) {
    return false;
  }
  return "dataBinding" in block && Boolean(block.dataBinding?.operationId?.trim());
}

/** União de schemas das fontes (sem repetir chave; paginação excluída). */
export function buildMultiSourceParamSchema(
  routes: TvDataRouteCatalogItem[],
  targets: MultiSourceBindingTarget[],
): DataParamSchema {
  const operationIds = targets
    .map((block) => String(block.dataBinding.operationId || "").trim())
    .filter(Boolean);
  return mergeRouteParamSchemas(routes, operationIds);
}

/**
 * Valores exibidos na multi-seleção: se todas as fontes concordam, mostra o valor;
 * se divergem, string vazia + chave em `divergedKeys` (UI: «Valores diferentes»).
 * Inclui `dateRangePreset` (sintetizador) quando o schema união tem par de datas.
 */
export function resolveSharedParamDisplayValues(
  targets: MultiSourceBindingTarget[],
  schema: DataParamSchema,
): { values: Record<string, string>; divergedKeys: Set<string> } {
  const values: Record<string, string> = {};
  const divergedKeys = new Set<string>();
  const keys = new Set(Object.keys(schema));
  if (findDateRangeKeys(keys)) {
    keys.add(DATE_RANGE_PRESET_PARAM);
    keys.add(PERIOD_DAYS_PARAM);
  }
  for (const key of keys) {
    if (AGGREGATE_EXCLUDED_PARAM_KEYS.has(key)) continue;
    let shared: string | null = null;
    let diverged = false;
    for (const target of targets) {
      const raw = target.dataBinding.params?.[key];
      const text = raw === undefined || raw === null ? "" : String(raw);
      if (shared === null) shared = text;
      else if (shared !== text) {
        diverged = true;
        break;
      }
    }
    if (diverged) divergedKeys.add(key);
    values[key] = diverged ? "" : (shared ?? "");
  }
  return { values, divergedKeys };
}

/** Schema visível de uma rota (para aplicar só chaves que a fonte aceita). */
export function resolveTargetParamSchema(
  routes: TvDataRouteCatalogItem[],
  target: MultiSourceBindingTarget,
): DataParamSchema {
  const operationId = String(target.dataBinding.operationId || "").trim();
  const route = routes.find((item) => item.operationId === operationId);
  if (!route?.paramSchema) return {};
  return visibleParamSchema(
    route.paramSchema as DataParamSchema,
    route.fixedQueryParams as Record<string, unknown> | undefined,
  );
}

/**
 * Traduz updates da UI multi-fonte para chaves que a rota aceita.
 * `dateRangePreset` / `periodDays` não vêm do OpenAPI — aplicam em rotas com par de datas.
 * Datas limpas pelo sintetizador (aliases da união) são remapeadas ao par da rota.
 */
export function mapUpdatesToTargetSchema(
  schema: DataParamSchema,
  updates: Record<string, string>,
): Record<string, string> {
  const applicable: Record<string, string> = {};
  const pair = findDateRangeKeys(Object.keys(schema));

  for (const [key, raw] of Object.entries(updates)) {
    if (schema[key]) applicable[key] = raw;
  }

  if (!pair) return applicable;

  if (Object.prototype.hasOwnProperty.call(updates, DATE_RANGE_PRESET_PARAM)) {
    applicable[DATE_RANGE_PRESET_PARAM] = updates[DATE_RANGE_PRESET_PARAM];
  }
  if (Object.prototype.hasOwnProperty.call(updates, PERIOD_DAYS_PARAM)) {
    applicable[PERIOD_DAYS_PARAM] = updates[PERIOD_DAYS_PARAM];
  }

  const dateUpdate = readDateRangeUpdateValues(updates);
  if (dateUpdate.hasStart) applicable[pair.startKey] = dateUpdate.start;
  if (dateUpdate.hasEnd) applicable[pair.endKey] = dateUpdate.end;

  return applicable;
}

/**
 * Monta patches atômicos: cada fonte recebe só as chaves que aceita
 * (schema OpenAPI + sintetizador de período quando há intervalo de datas).
 */
export function buildMultiSourceParamPatches(
  targets: MultiSourceBindingTarget[],
  routes: TvDataRouteCatalogItem[],
  updates: Record<string, string>,
): Array<{ blockId: string; patch: Partial<ComunicadoBlock> }> {
  const patches: Array<{ blockId: string; patch: Partial<ComunicadoBlock> }> = [];
  for (const target of targets) {
    const schema = resolveTargetParamSchema(routes, target);
    const applicable = mapUpdatesToTargetSchema(schema, updates);
    if (Object.keys(applicable).length === 0) continue;
    const nextParams = applyDataParamRawUpdates(target.dataBinding.params, applicable, schema);
    patches.push({
      blockId: target.id,
      patch: {
        dataBinding: { ...target.dataBinding, params: nextParams },
      } as Partial<ComunicadoBlock>,
    });
  }
  return patches;
}
