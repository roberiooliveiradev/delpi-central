import type {
  ComunicadoBlock,
  ComunicadoConfig,
  ComunicadoDataBinding,
  DataSourceLabelRouteInfo,
} from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";

/** Aliases legado → canônico HTTP (alinhado à TV API). */
const PARAM_KEY_REMAP: Record<string, string> = {
  date_start: "start_date",
  date_end: "end_date",
  dataInicio: "start_date",
  dataFim: "end_date",
  data_inicio: "start_date",
  data_fim: "end_date",
  data_inicial: "start_date",
  data_final: "end_date",
  date_from: "start_date",
  date_to: "end_date",
};

const INTERNAL_PARAM_KEYS = new Set(["dateRangePreset", "periodDays"]);

function isCatalogLikeLabel(
  label: string | null | undefined,
  route: DataSourceLabelRouteInfo | null | undefined,
): boolean {
  const trimmed = String(label ?? "").trim();
  if (!trimmed) return true;
  if (!route) return false;
  const current = String(route.label ?? "").trim();
  if (current && trimmed === current) return true;
  const aliases = Array.isArray(route.labelAliases) ? route.labelAliases : [];
  return aliases.some((alias) => String(alias ?? "").trim() === trimmed);
}

export type HydrateDataBindingsResult = {
  config: ComunicadoConfig;
  changed: boolean;
  orphanOperationIds: string[];
  strippedParamKeys: string[];
  remappedParamKeys: string[];
  clearedLabels: number;
};

function routeInfoFromCatalog(
  routes: Iterable<TvDataRouteCatalogItem>,
): Map<string, TvDataRouteCatalogItem> {
  const map = new Map<string, TvDataRouteCatalogItem>();
  for (const route of routes) {
    const id = String(route.operationId || "").trim();
    if (id) map.set(id, route);
  }
  return map;
}

function hydrateBindingParams(
  params: Record<string, string | number | boolean | null | undefined> | undefined,
  route: TvDataRouteCatalogItem | undefined,
): {
  params: Record<string, string | number | boolean>;
  stripped: string[];
  remapped: string[];
} {
  const raw = { ...(params ?? {}) };
  const remapped: string[] = [];
  const schema = (route?.paramSchema ?? {}) as Record<string, unknown>;
  const schemaKeys = new Set(Object.keys(schema));
  const fixed = route?.fixedQueryParams ?? {};

  for (const [legacy, canonical] of Object.entries(PARAM_KEY_REMAP)) {
    if (!(legacy in raw)) continue;
    if (schemaKeys.size > 0 && !schemaKeys.has(canonical) && schemaKeys.has(legacy)) {
      continue;
    }
    const value = raw[legacy];
    delete raw[legacy];
    remapped.push(`${legacy}→${canonical}`);
    if (value === undefined || value === null || value === "") continue;
    if (raw[canonical] === undefined || raw[canonical] === null || raw[canonical] === "") {
      raw[canonical] = value;
    }
  }

  const stripped: string[] = [];
  const next: Record<string, string | number | boolean> = {};
  for (const [key, value] of Object.entries(raw)) {
    if (value === undefined || value === null || value === "") continue;
    if (INTERNAL_PARAM_KEYS.has(key)) {
      next[key] = value as string | number | boolean;
      continue;
    }
    if (key in fixed) continue;
    if (schemaKeys.size > 0 && !schemaKeys.has(key)) {
      stripped.push(key);
      continue;
    }
    next[key] = value as string | number | boolean;
  }

  // Defaults do catálogo / schema para chaves ainda vazias (não sobrescreve).
  const defaults = route?.defaultParams ?? {};
  for (const [key, value] of Object.entries(defaults)) {
    if (value === undefined || value === null || value === "") continue;
    if (key in fixed) continue;
    if (next[key] === undefined) next[key] = value as string | number | boolean;
  }
  for (const [key, spec] of Object.entries(schema)) {
    if (key in fixed) continue;
    if (next[key] !== undefined) continue;
    if (!spec || typeof spec !== "object") continue;
    const def = (spec as { default?: unknown }).default;
    if (def !== undefined && def !== null && def !== "") {
      next[key] = def as string | number | boolean;
    }
  }

  return { params: next, stripped, remapped };
}

function hydrateOneBinding(
  binding: ComunicadoDataBinding,
  route: TvDataRouteCatalogItem | undefined,
): {
  binding: ComunicadoDataBinding;
  changed: boolean;
  orphan: boolean;
  stripped: string[];
  remapped: string[];
  clearedLabel: boolean;
} {
  const operationId = String(binding.operationId || "").trim();
  const orphan = Boolean(operationId) && !route;
  let changed = false;
  let clearedLabel = false;
  const next: ComunicadoDataBinding = { ...binding };

  const routeInfo: DataSourceLabelRouteInfo | null = route
    ? { label: route.label, labelAliases: route.labelAliases }
    : null;
  if (isCatalogLikeLabel(binding.label, routeInfo)) {
    if (binding.label != null && binding.label !== "") {
      delete next.label;
      changed = true;
      clearedLabel = true;
    }
  }

  const { params, stripped, remapped } = hydrateBindingParams(binding.params, route);
  const prevParams = binding.params ?? {};
  const prevKeys = Object.keys(prevParams).sort().join(",");
  const nextKeys = Object.keys(params).sort().join(",");
  const paramsChanged =
    prevKeys !== nextKeys ||
    nextKeys.split(",").some((key) => key && String(prevParams[key]) !== String(params[key]));
  if (paramsChanged) {
    next.params = params;
    changed = true;
  }

  return {
    binding: next,
    changed,
    orphan,
    stripped,
    remapped,
    clearedLabel,
  };
}

/**
 * Alinha dataBindings ao catálogo vivo (labels catalog-like, aliases de data, strip de params).
 * Idempotente — safe no load do editor e antes do save.
 */
export function hydrateComunicadoDataBindings(
  config: ComunicadoConfig,
  routes: Iterable<TvDataRouteCatalogItem>,
): HydrateDataBindingsResult {
  const byId = routeInfoFromCatalog(routes);
  const orphanOperationIds: string[] = [];
  const strippedParamKeys: string[] = [];
  const remappedParamKeys: string[] = [];
  let clearedLabels = 0;
  let changed = false;

  const blocks = (config.blocks ?? []).map((block) => {
    if (!("dataBinding" in block) || !block.dataBinding) return block;
    const operationId = String(block.dataBinding.operationId || "").trim();
    const route = byId.get(operationId);
    const result = hydrateOneBinding(block.dataBinding, route);
    if (result.orphan && operationId) orphanOperationIds.push(operationId);
    strippedParamKeys.push(...result.stripped);
    remappedParamKeys.push(...result.remapped);
    if (result.clearedLabel) clearedLabels += 1;
    if (!result.changed) return block;
    changed = true;
    return { ...block, dataBinding: result.binding } as ComunicadoBlock;
  });

  // dataFilters do slide: mesmos remaps/strips contra união de schemas (só remap + drop unknown comuns).
  let dataFilters = config.dataFilters;
  if (dataFilters && typeof dataFilters === "object") {
    const unionSchema: Record<string, unknown> = {};
    for (const route of byId.values()) {
      Object.assign(unionSchema, route.paramSchema ?? {});
    }
    const fakeRoute = {
      operationId: "__slide__",
      label: "",
      category: "",
      paramSchema: unionSchema,
    } as TvDataRouteCatalogItem;
    const filterResult = hydrateBindingParams(
      dataFilters as Record<string, string | number | boolean | null | undefined>,
      fakeRoute,
    );
    const prev = JSON.stringify(dataFilters);
    const next = filterResult.params;
    if (JSON.stringify(next) !== prev) {
      dataFilters = Object.keys(next).length > 0 ? next : undefined;
      changed = true;
      strippedParamKeys.push(...filterResult.stripped);
      remappedParamKeys.push(...filterResult.remapped);
    }
  }

  return {
    config: changed ? { ...config, blocks, dataFilters } : config,
    changed,
    orphanOperationIds: [...new Set(orphanOperationIds)],
    strippedParamKeys: [...new Set(strippedParamKeys)],
    remappedParamKeys: [...new Set(remappedParamKeys)],
    clearedLabels,
  };
}

export function buildLabelCatalogFromRoutes(
  routes: Iterable<TvDataRouteCatalogItem>,
): Record<string, DataSourceLabelRouteInfo> {
  const out: Record<string, DataSourceLabelRouteInfo> = {};
  for (const route of routes) {
    const id = String(route.operationId || "").trim();
    if (!id) continue;
    out[id] = { label: route.label, labelAliases: route.labelAliases };
  }
  return out;
}
