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

/** Espelho de `BRANCH_PARAM_KEYS` na TV API (`comunicado_data_params_service`). */
const BRANCH_PARAM_KEYS = new Set(["branch", "filial", "branch_code", "filial_id"]);

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

export type HydrateDataBindingPatch = {
  blockId: string;
  dataBinding: ComunicadoDataBinding;
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

function stableRecordJson(
  value: Record<string, string | number | boolean | null | undefined> | undefined,
): string {
  if (!value || typeof value !== "object") return "{}";
  const keys = Object.keys(value).sort();
  const normalized: Record<string, string | number | boolean> = {};
  for (const key of keys) {
    const entry = value[key];
    if (entry === undefined || entry === null || entry === "") continue;
    normalized[key] = entry as string | number | boolean;
  }
  return JSON.stringify(normalized);
}

function canonicalBranchWireValue(value: unknown): string | null {
  if (value === undefined || value === null) return null;
  const raw = String(value).trim();
  if (!raw) return null;
  if (["all", "todas", "todos"].includes(raw.toLowerCase())) return "all";
  return raw;
}

function resolveAnyBranchValue(
  params: Record<string, string | number | boolean | null | undefined>,
): unknown {
  for (const key of BRANCH_PARAM_KEYS) {
    if (!(key in params)) continue;
    const value = params[key];
    if (value === undefined || value === null || value === "") continue;
    if (String(value).trim()) return value;
  }
  return null;
}

/**
 * Projeta filial de qualquer alias para as chaves do paramSchema da rota.
 * Alinhado a `project_branch_params_onto_route_schema` na TV API — evita strip
 * de `branch` perder o valor quando a rota só declara `filial` / `filial_id`.
 */
export function projectBranchParamsOntoRouteSchema(
  params: Record<string, string | number | boolean | null | undefined>,
  schemaKeys: Set<string>,
): Record<string, string | number | boolean | null | undefined> {
  const out: Record<string, string | number | boolean | null | undefined> = { ...params };
  const targets = [...schemaKeys].filter((key) => BRANCH_PARAM_KEYS.has(key));
  if (targets.length === 0) return out;
  const wire = canonicalBranchWireValue(resolveAnyBranchValue(out));
  for (const key of BRANCH_PARAM_KEYS) {
    delete out[key];
  }
  if (wire == null) return out;
  for (const key of targets) {
    out[key] = wire;
  }
  return out;
}

function hydrateBindingParams(
  params: Record<string, string | number | boolean | null | undefined> | undefined,
  route: TvDataRouteCatalogItem | undefined,
): {
  params: Record<string, string | number | boolean>;
  stripped: string[];
  remapped: string[];
} {
  let raw: Record<string, string | number | boolean | null | undefined> = {
    ...(params ?? {}),
  };
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

  if (schemaKeys.size > 0) {
    raw = projectBranchParamsOntoRouteSchema(raw, schemaKeys);
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
  // Só chaves do schema (ou internas) — evita reintroduzir `branch` fora do contrato.
  const defaults = route?.defaultParams ?? {};
  for (const [key, value] of Object.entries(defaults)) {
    if (value === undefined || value === null || value === "") continue;
    if (key in fixed) continue;
    if (
      schemaKeys.size > 0 &&
      !schemaKeys.has(key) &&
      !INTERNAL_PARAM_KEYS.has(key)
    ) {
      continue;
    }
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
  const paramsChanged = stableRecordJson(prevParams) !== stableRecordJson(params);
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
 * Fingerprint estável do que o hydrate lê — não do resultado (stripped/changed).
 * Usado para não reaplicar hydrate a cada tick de config idêntico em conteúdo.
 */
export function buildHydrateBindingsInputFingerprint(
  config: ComunicadoConfig,
  routes: Iterable<TvDataRouteCatalogItem>,
): string {
  const routeIds = [...routeInfoFromCatalog(routes).keys()].sort();
  const bindings = (config.blocks ?? [])
    .filter((block) => "dataBinding" in block && block.dataBinding)
    .map((block) => {
      const binding = (block as { id: string; dataBinding: ComunicadoDataBinding }).dataBinding;
      return {
        id: block.id,
        operationId: binding.operationId ?? "",
        label: binding.label ?? null,
        params: stableRecordJson(binding.params),
      };
    })
    .sort((a, b) => a.id.localeCompare(b.id));
  return JSON.stringify({
    routeIds,
    dataFilters: stableRecordJson(
      (config.dataFilters ?? undefined) as
        | Record<string, string | number | boolean | null | undefined>
        | undefined,
    ),
    bindings,
  });
}

/** Patches mínimos (`dataBinding` only) — evita regravar bloco inteiro no editor. */
export function collectHydrateDataBindingPatches(
  before: ComunicadoConfig,
  after: ComunicadoConfig,
): HydrateDataBindingPatch[] {
  const beforeById = new Map(
    (before.blocks ?? [])
      .filter((block) => "dataBinding" in block && block.dataBinding)
      .map((block) => [block.id, (block as { dataBinding: ComunicadoDataBinding }).dataBinding]),
  );
  const patches: HydrateDataBindingPatch[] = [];
  for (const block of after.blocks ?? []) {
    if (!("dataBinding" in block) || !block.dataBinding) continue;
    const prev = beforeById.get(block.id);
    if (!prev) continue;
    if (JSON.stringify(prev) === JSON.stringify(block.dataBinding)) continue;
    patches.push({ blockId: block.id, dataBinding: block.dataBinding });
  }
  return patches;
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
    const prev = stableRecordJson(
      dataFilters as Record<string, string | number | boolean | null | undefined>,
    );
    const next = filterResult.params;
    if (stableRecordJson(next) !== prev) {
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

/**
 * Sessão do editor: ribbon + painel lateral montam o mesmo hydrate.
 * Fingerprint compartilhado evita apply duplicado no mesmo input.
 */
let sessionHydrateOutputFp = "";
let sessionHydrateInFlightFp = "";
/** Input já consumido neste apply — efeito gêmeo (ribbon) ainda vê o config pré-hydrate. */
let sessionHydrateConsumedInputFp = "";

/** Só testes. */
export function resetHydrateBindingsSessionFingerprintForTests(): void {
  sessionHydrateOutputFp = "";
  sessionHydrateInFlightFp = "";
  sessionHydrateConsumedInputFp = "";
}

export type HydrateBindingsApplyPlan = {
  patches: HydrateDataBindingPatch[];
  dataFilters?: ComunicadoConfig["dataFilters"];
  dataFiltersChanged: boolean;
  hint: boolean;
  result: HydrateDataBindingsResult;
  inputFp: string;
  outputFp: string;
};

/**
 * Planeja hydrate idempotente para o painel Dados (uma vez por fingerprint de input).
 */
export function planHydrateBindingsApply(
  config: ComunicadoConfig,
  routes: Iterable<TvDataRouteCatalogItem>,
): HydrateBindingsApplyPlan | null {
  const inputFp = buildHydrateBindingsInputFingerprint(config, routes);
  if (
    inputFp === sessionHydrateOutputFp ||
    inputFp === sessionHydrateInFlightFp ||
    inputFp === sessionHydrateConsumedInputFp
  ) {
    return null;
  }
  const result = hydrateComunicadoDataBindings(config, routes);
  if (!result.changed) {
    sessionHydrateOutputFp = inputFp;
    return null;
  }
  sessionHydrateInFlightFp = inputFp;
  const patches = collectHydrateDataBindingPatches(config, result.config);
  const dataFiltersChanged = result.config.dataFilters !== config.dataFilters;
  const outputFp = buildHydrateBindingsInputFingerprint(result.config, routes);
  return {
    patches,
    dataFilters: result.config.dataFilters,
    dataFiltersChanged,
    hint:
      result.clearedLabels > 0 ||
      result.remappedParamKeys.length > 0 ||
      result.strippedParamKeys.length > 0,
    result,
    inputFp,
    outputFp,
  };
}

export function commitHydrateBindingsApplyPlan(plan: HydrateBindingsApplyPlan): void {
  sessionHydrateOutputFp = plan.outputFp;
  sessionHydrateConsumedInputFp = plan.inputFp;
  if (sessionHydrateInFlightFp === plan.inputFp) {
    sessionHydrateInFlightFp = "";
  }
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
