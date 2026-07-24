import type { ComunicadoDataBinding } from "@delpi/tv-dashboard-presentation";

import type { TvDataRouteCatalogItem } from "../api/tvDashboardApi";
import {
  DATE_RANGE_PRESET_PARAM,
  defaultDateRangePreset,
  findDateRangeKeys,
} from "./dateRangePresets";

/** Valores seguros para obrigatórios recorrentes quando o schema não traz default. */
export const CONVENIENT_REQUIRED_DEFAULTS: Record<string, string> = {
  branch: "01",
  filial: "01",
  branch_code: "01",
  department_id: "commercial",
  q: "pac",
  description: "codigo",
};

const BRANCH_DEFAULT_BY_PATH_PREFIX: Array<[string, string]> = [["/scheduling/", "SC"]];

function branchDefaultForRoute(route: TvDataRouteCatalogItem): string {
  const path = String(route.path ?? "").trim();
  for (const [prefix, value] of BRANCH_DEFAULT_BY_PATH_PREFIX) {
    if (path.startsWith(prefix)) return value;
  }
  return CONVENIENT_REQUIRED_DEFAULTS.branch;
}

function convenientDefault(key: string, route: TvDataRouteCatalogItem): string | undefined {
  if (key === "branch") return branchDefaultForRoute(route);
  return CONVENIENT_REQUIRED_DEFAULTS[key];
}

type ParamValue = string | number | boolean;

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
    defaults[key] = value as ParamValue;
  }

  const schema = route.paramSchema ?? {};
  for (const [key, raw] of Object.entries(schema)) {
    const spec = raw as { default?: ParamValue; optional?: boolean };
    if (defaults[key] !== undefined && defaults[key] !== "") continue;
    if (spec?.default !== undefined) {
      defaults[key] = spec.default;
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
  const competenceFirst = "competence" in schema;
  const preset = competenceFirst ? null : defaultDateRangePreset(pair);
  if (preset) {
    defaults[DATE_RANGE_PRESET_PARAM] = preset;
  }
  return defaults;
}
