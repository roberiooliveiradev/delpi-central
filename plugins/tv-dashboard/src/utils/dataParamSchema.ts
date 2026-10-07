/**
 * Schema de parâmetros de dados — tipos e helpers puros (sem componente).
 *
 * Owner canônico das projeções de schema: filtro de fixedQueryParams,
 * injeção de `excludeWeekends`, opções de enum/boolean e labels de opção.
 * `DataParamFields` é o editor visual; esta camada é compartilhada por
 * ribbon, inspector, playlist e data models.
 */
import {
  EXCLUDE_WEEKENDS_PARAM,
  routeSupportsDailyGranularity,
} from "@delpi/tv-dashboard-presentation";

import {
  ENUM_OPTION_LABELS,
  UI_FALLBACK_ENUMS,
} from "../content/dataParamCatalog";
import {
  PERIOD_DAYS_PARAM,
  type DateRangePresetId,
} from "./dateRangePresets";

export type DataParamSchemaField = {
  type?: string;
  label?: string;
  description?: string;
  default?: string | number | boolean;
  optional?: boolean;
  enum?: Array<string | number | boolean>;
  /** Rótulo por valor (chave = `String(valor)`); vence o catálogo de rótulos por chave. */
  enumLabels?: Record<string, string>;
  /** `in: path` — parâmetro de path, nunca editável por expressão. */
  in?: string;
  /** Opt-out do contrato — expressionAllowed=false no paramSchema. */
  expressionAllowed?: boolean;
  format?: string;
};

export type DataParamSchema = Record<string, DataParamSchemaField>;

/** Máximo de campos inline na ribbon; acima disso abre modal. */
export const RIBBON_INLINE_PARAM_LIMIT = 4;

const EXCLUDE_WEEKENDS_FIELD: DataParamSchemaField = {
  type: "boolean",
  optional: true,
  enum: [true, false],
};

export function enumOptionLabel(paramKey: string, value: string): string {
  return ENUM_OPTION_LABELS[paramKey]?.[value] ?? value;
}

export function resolveParamSelectOptions(
  key: string,
  field: DataParamSchemaField,
): Array<{ value: string; label: string }> | null {
  // Período em dias: sempre input numérico (qualquer valor positivo).
  if (key === PERIOD_DAYS_PARAM) return null;

  const rawEnum = Array.isArray(field.enum)
    ? field.enum.filter((item) => item !== null && item !== undefined)
    : [];
  const values =
    rawEnum.length > 0
      ? rawEnum
      : field.type === "boolean"
        ? [true, false]
        : (UI_FALLBACK_ENUMS[key] ?? null);
  if (!values || values.length === 0) return null;

  if (field.type === "boolean" || values.every((item) => typeof item === "boolean")) {
    return values.map((item) => ({
      value: String(item),
      label: item === true || String(item) === "true" ? "Sim" : "Não",
    }));
  }

  return values.map((item) => {
    const value = String(item);
    return { value, label: field.enumLabels?.[value] ?? enumOptionLabel(key, value) };
  });
}

/** @deprecated Preferir rótulos em helpTooltips; mantido para testes de contrato. */
export function resolveFallbackPreset(openEndedDateRange: boolean): DateRangePresetId {
  return openEndedDateRange ? "custom" : "this_month";
}

/** Injeta o boolean visual quando a rota admite granularidade diária. */
export function withExcludeWeekendsSchemaField(
  schema: DataParamSchema,
  options?: {
    fullSchema?: DataParamSchema;
    fixedQueryParams?: Record<string, unknown> | null;
  },
): DataParamSchema {
  const full = options?.fullSchema ?? schema;
  if (!routeSupportsDailyGranularity(full, options?.fixedQueryParams)) return schema;
  if (schema[EXCLUDE_WEEKENDS_PARAM]) return schema;
  return {
    ...schema,
    [EXCLUDE_WEEKENDS_PARAM]: EXCLUDE_WEEKENDS_FIELD,
  };
}

export function visibleParamSchema(
  schema: DataParamSchema | undefined | null,
  fixedQueryParams?: Record<string, unknown> | null,
): DataParamSchema {
  const base = (schema ?? {}) as DataParamSchema;
  const fixed = fixedQueryParams ?? {};
  const visible =
    !fixed || Object.keys(fixed).length === 0
      ? base
      : (Object.fromEntries(
          Object.entries(base).filter(([key]) => !(key in fixed)),
        ) as DataParamSchema);
  return withExcludeWeekendsSchemaField(visible, {
    fullSchema: base,
    fixedQueryParams: fixed,
  });
}
