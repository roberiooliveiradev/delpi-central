import {
  EXCLUDE_WEEKENDS_PARAM,
  type DataParamValue,
  type TvDataModel,
  type TvDataModelInput,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  applyDataParamRawUpdates,
  type DataParamUpdateValue,
} from "./applyDataParamUpdates";
import {
  AGGREGATE_EXCLUDED_PARAM_KEYS,
  mergeRouteParamSchemasDetailed,
  type RouteParamSchemaConflict,
} from "./collectPlaylistDataParamSchema";
import {
  visibleParamSchema,
  type DataParamSchema,
} from "./dataParamSchema";
import {
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
} from "./dateRangePresets";
import { mapUpdatesToTargetSchema } from "./multiSourceDataParams";
import { isParamExpressionValue, paramAllowsExpression } from "./paramExpressions";

/**
 * Projeção «Filtros do modelo» sobre `dataModels[].inputs[]` — camada de UI
 * apenas; o owner persistido continua sendo `inputs[].params`. Edição
 * agregada faz fan-out mínimo para os inputs cujo schema aceita a chave
 * (mesma regra da multi-seleção: `mapUpdatesToTargetSchema` +
 * `applyDataParamRawUpdates`). Nenhum campo novo é persistido no modelo.
 */

/** operationIds das rotas usadas pelos inputs do modelo (dedup, ordem estável). */
export function resolveDataModelOperationIds(model: TvDataModel): string[] {
  const ids = new Set<string>();
  for (const input of model.inputs ?? []) {
    const operationId = String(input.operationId ?? "").trim();
    if (operationId) ids.add(operationId);
  }
  return [...ids];
}

/**
 * Schema agregado do modelo (campos compartilháveis entre inputs) +
 * conflitos de schema incompatível — mesma política do merge de slide/
 * programação: compatível mergeia, incompatível sai do agregado e volta
 * como metadado de conflito para feedback.
 */
export function collectDataModelParamSchema(
  routes: TvDataRouteCatalogItem[],
  model: TvDataModel,
): { schema: DataParamSchema; conflicts: RouteParamSchemaConflict[] } {
  return mergeRouteParamSchemasDetailed(routes, resolveDataModelOperationIds(model));
}

/** Rota de referência do modelo para flags de UI (período aberto etc.). */
export function resolveModelPrimaryRoute(
  routes: TvDataRouteCatalogItem[],
  model: TvDataModel,
): TvDataRouteCatalogItem | null {
  const byId = new Map(routes.map((route) => [route.operationId, route] as const));
  const primary = model.inputs.find((input) => input.id === model.primaryInputId);
  return byId.get(primary?.operationId ?? "") ?? byId.get(model.inputs[0]?.operationId ?? "") ?? null;
}

function inputVisibleSchema(
  routes: TvDataRouteCatalogItem[],
  input: TvDataModelInput,
): DataParamSchema {
  const route = routes.find((item) => item.operationId === input.operationId);
  if (!route?.paramSchema) return {};
  return visibleParamSchema(
    route.paramSchema as DataParamSchema,
    route.fixedQueryParams as Record<string, unknown> | undefined,
  );
}

/** Chaves sintetizadas pela UI (não existem no OpenAPI, mas valem para todo input). */
function isSynthesizedParamKey(key: string): boolean {
  return (
    key === DATE_RANGE_PRESET_PARAM ||
    key === PERIOD_DAYS_PARAM ||
    key === EXCLUDE_WEEKENDS_PARAM
  );
}

function paramValueEquals(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  const aMissing = a === undefined || a === null || a === "";
  const bMissing = b === undefined || b === null || b === "";
  if (aMissing && bMissing) return true;
  if (isParamExpressionValue(a) && isParamExpressionValue(b)) {
    return JSON.stringify(a) === JSON.stringify(b);
  }
  return String(a ?? "") === String(b ?? "");
}

/**
 * Valores exibidos no filtro agregado do modelo: compartilhado quando todos
 * os inputs compatíveis concordam (inclui ExpressionSpec intacto); divergente
 * vira `""` + chave em `divergedKeys`. `partialKeys` = chave aceita só por
 * parte dos inputs — a UI explicita o escopo.
 */
export function resolveModelSharedParamValues(
  model: TvDataModel,
  routes: TvDataRouteCatalogItem[],
  schema: DataParamSchema,
): {
  values: Record<string, DataParamValue | null | undefined>;
  divergedKeys: Set<string>;
  partialKeys: Set<string>;
} {
  const inputSchemas = model.inputs.map((input) => inputVisibleSchema(routes, input));
  const keys = new Set(Object.keys(schema));
  if (findDateRangeKeys(keys)) {
    keys.add(DATE_RANGE_PRESET_PARAM);
    keys.add(PERIOD_DAYS_PARAM);
  }
  if ("granularity" in schema) keys.add(EXCLUDE_WEEKENDS_PARAM);

  const values: Record<string, DataParamValue | null | undefined> = {};
  const divergedKeys = new Set<string>();
  const partialKeys = new Set<string>();
  for (const key of keys) {
    if (AGGREGATE_EXCLUDED_PARAM_KEYS.has(key)) continue;
    const applicable = isSynthesizedParamKey(key)
      ? model.inputs.map((_, index) => index)
      : model.inputs
          .map((_, index) => index)
          .filter((index) => Boolean(inputSchemas[index]?.[key]));
    if (applicable.length === 0) continue;
    if (applicable.length < model.inputs.length) partialKeys.add(key);
    const first = model.inputs[applicable[0]!]?.params?.[key];
    const diverged = applicable
      .slice(1)
      .some((index) => !paramValueEquals(model.inputs[index]?.params?.[key], first));
    if (diverged) divergedKeys.add(key);
    values[key] = diverged ? "" : first;
  }
  return { values, divergedKeys, partialKeys };
}

/**
 * Traduz updates agregados do modelo para o patch mínimo por input:
 * aplica só chaves aceitas pelo schema visível da rota do input (preset de
 * período sempre vale — sintetizador), preserva os demais params e campos
 * do input/modelo. ExpressionSpec só entra em inputs cuja rota permite.
 * Retorna `null` quando nenhum input aceita nenhuma chave.
 */
export function buildDataModelParamPatch(
  model: TvDataModel,
  routes: TvDataRouteCatalogItem[],
  updates: Record<string, DataParamUpdateValue>,
): TvDataModel | null {
  let touched = false;
  const inputs = model.inputs.map((input) => {
    const route = routes.find((item) => item.operationId === input.operationId);
    const schema = inputVisibleSchema(routes, input);
    const fixedKeys = new Set(Object.keys(route?.fixedQueryParams ?? {}));

    const literalUpdates: Record<string, string> = {};
    const expressionUpdates: Record<string, DataParamUpdateValue> = {};
    for (const [key, raw] of Object.entries(updates)) {
      if (isParamExpressionValue(raw)) expressionUpdates[key] = raw;
      else literalUpdates[key] = String(raw ?? "");
    }

    const applicable: Record<string, DataParamUpdateValue> = {
      ...mapUpdatesToTargetSchema(schema, literalUpdates),
    };
    for (const [key, spec] of Object.entries(expressionUpdates)) {
      if (schema[key] && paramAllowsExpression(key, schema[key], fixedKeys)) {
        applicable[key] = spec;
      }
    }
    if (Object.keys(applicable).length === 0) return input;

    const nextParams = applyDataParamRawUpdates(input.params, applicable, schema);
    if (stableParamsJson(nextParams) === stableParamsJson(input.params)) return input;
    touched = true;
    return { ...input, params: nextParams as Record<string, DataParamValue> };
  });
  return touched ? { ...model, inputs } : null;
}

function stableParamsJson(params: Record<string, unknown> | undefined): string {
  const normalized: Record<string, unknown> = {};
  for (const key of Object.keys(params ?? {}).sort()) {
    const value = params?.[key];
    if (value !== undefined && value !== null && value !== "") normalized[key] = value;
  }
  return JSON.stringify(normalized);
}
