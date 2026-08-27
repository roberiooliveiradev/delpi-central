/**
 * Defaults de paramSchema / defaultParams — espelho de
 * `tv_data_param_defaults_service.py` (TV API).
 *
 * Filtros opcionais nunca são inventados no bloco Dados («Não definido aqui»);
 * a api-delpi aplica o default do Query quando o param é omitido no wire.
 */

import { PERIOD_DAYS_PARAM } from "./dateRangePresets";

export type ParamSchemaSpec = {
  default?: string | number | boolean | null;
  optional?: boolean;
  enum?: unknown[];
};

/** Select de identidade: nunca inventar (ex.: department_id → commercial). */
const NO_SCHEMA_DEFAULT_KEYS = new Set(["department_id"]);

export function isOptionalParamSpec(spec: ParamSchemaSpec | null | undefined): boolean {
  if (!spec) return true;
  return spec.optional !== false;
}

/** Defaults OpenAPI/catálogo só para params obrigatórios. */
export function shouldApplySchemaDefault(key: string, spec: ParamSchemaSpec): boolean {
  if (spec.default === undefined || spec.default === null || spec.default === "") {
    return false;
  }
  if (NO_SCHEMA_DEFAULT_KEYS.has(key) || key === PERIOD_DAYS_PARAM) return false;
  if (isOptionalParamSpec(spec)) return false;
  return true;
}

/** defaultParams do catálogo: ignora chaves opcionais do schema (todas as rotas). */
export function shouldApplyCatalogDefaultParam(
  key: string,
  spec: ParamSchemaSpec | null | undefined,
): boolean {
  if (key === PERIOD_DAYS_PARAM) return false;
  if (spec && isOptionalParamSpec(spec)) return false;
  return true;
}
