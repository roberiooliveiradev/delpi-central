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
 * se divergem, string vazia (usuário define um valor comum).
 */
export function resolveSharedParamDisplayValues(
  targets: MultiSourceBindingTarget[],
  schema: DataParamSchema,
): Record<string, string> {
  const values: Record<string, string> = {};
  for (const key of Object.keys(schema)) {
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
    values[key] = diverged ? "" : (shared ?? "");
  }
  return values;
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
 * Monta patches atômicos: cada fonte recebe só as chaves do seu schema.
 * Chaves que a fonte não tem são ignoradas (união na UI, aplicação seletiva).
 */
export function buildMultiSourceParamPatches(
  targets: MultiSourceBindingTarget[],
  routes: TvDataRouteCatalogItem[],
  updates: Record<string, string>,
): Array<{ blockId: string; patch: Partial<ComunicadoBlock> }> {
  const patches: Array<{ blockId: string; patch: Partial<ComunicadoBlock> }> = [];
  for (const target of targets) {
    const schema = resolveTargetParamSchema(routes, target);
    const applicable: Record<string, string> = {};
    for (const [key, raw] of Object.entries(updates)) {
      if (schema[key]) applicable[key] = raw;
    }
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
