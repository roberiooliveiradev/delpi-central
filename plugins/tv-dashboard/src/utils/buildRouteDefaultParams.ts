import type { ComunicadoDataBinding } from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
} from "./dateRangePresets";

/** Valores seguros para obrigatórios recorrentes quando o schema não traz default. */
export const CONVENIENT_REQUIRED_DEFAULTS: Record<string, string> = {
  branch: "01",
  filial: "01",
  branch_code: "01",
  q: "pac",
  description: "codigo",
};

type ParamValue = string | number | boolean;

/** Select de identidade: nunca inventar (ex.: department_id → commercial). */
const NO_SCHEMA_DEFAULT_KEYS = new Set(["department_id"]);

function shouldApplySchemaDefault(
  key: string,
  spec: { default?: ParamValue; optional?: boolean; enum?: unknown[] },
): boolean {
  if (spec.default === undefined || spec.default === null || spec.default === "") {
    return false;
  }
  if (NO_SCHEMA_DEFAULT_KEYS.has(key) || key === PERIOD_DAYS_PARAM) return false;
  const hasEnum = Array.isArray(spec.enum) && spec.enum.length > 0;
  // Select opcional: limpar não reverte para default de catálogo.
  if (hasEnum && spec.optional !== false) return false;
  return true;
}

const BRANCH_DEFAULT_BY_PATH_PREFIX: Array<[string, string]> = [["/scheduling/", "SC"]];

function branchDefaultForRoute(route: TvDataRouteCatalogItem): string {
  const path = String(route.path ?? "").trim();
  for (const [prefix, value] of BRANCH_DEFAULT_BY_PATH_PREFIX) {
    if (path.startsWith(prefix)) return value;
  }
  const schema = route.paramSchema ?? {};
  for (const key of ["branch", "filial"] as const) {
    const branchSpec = schema[key] as { enum?: Array<string | number | boolean> } | undefined;
    const enumValues = Array.isArray(branchSpec?.enum)
      ? branchSpec.enum.map((item) => String(item))
      : [];
    if (enumValues.includes("all")) return "all";
  }
  return CONVENIENT_REQUIRED_DEFAULTS.branch;
}

function convenientDefault(key: string, route: TvDataRouteCatalogItem): string | undefined {
  if (key === "branch" || key === "filial") return branchDefaultForRoute(route);
  return CONVENIENT_REQUIRED_DEFAULTS[key];
}

/**
 * Params iniciais ao escolher/testar uma fonte: defaultParams do catálogo,
 * default do schema, convenções (filial) e preset de período quando houver par de datas.
 */
export function buildRouteDefaultParams(
  route: TvDataRouteCatalogItem,
): NonNullable<ComunicadoDataBinding["params"]> {
  const defaults: NonNullable<ComunicadoDataBinding["params"]> = {};
  const catalogDefaults = route.defaultParams ?? {};
  for (const [key, value] of Object.entries(catalogDefaults)) {
    if (value === undefined || value === null || value === "") continue;
    // periodDays nunca como default de catálogo — evita «últimos N dias» implícito.
    if (key === PERIOD_DAYS_PARAM) continue;
    defaults[key] = value as ParamValue;
  }

  const schema = route.paramSchema ?? {};
  for (const [key, raw] of Object.entries(schema)) {
    const spec = raw as { default?: ParamValue; optional?: boolean; enum?: unknown[] };
    if (defaults[key] !== undefined && defaults[key] !== "") continue;
    if (key === PERIOD_DAYS_PARAM) continue;
    if (shouldApplySchemaDefault(key, spec)) {
      defaults[key] = spec.default as ParamValue;
      continue;
    }
    if (spec?.optional === false) {
      const convenient = convenientDefault(key, route);
      if (convenient !== undefined) {
        defaults[key] = convenient;
      }
    }
  }

  const pair = findDateRangeKeys(Object.keys(schema));
  // Rotas open-ended: Personalizado sem datas = histórico completo.
  // Demais rotas: NÃO grava dateRangePreset no bloco — herda Programação/slide
  // (senão this_month/branch default sombreiam dataDefaults e o filtro «não funciona»).
  if (route.openEndedDateRange && pair) {
    defaults[DATE_RANGE_PRESET_PARAM] = "custom";
    delete defaults[PERIOD_DAYS_PARAM];
  }
  return defaults;
}
