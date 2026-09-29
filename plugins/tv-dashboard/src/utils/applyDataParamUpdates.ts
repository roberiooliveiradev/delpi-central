import {
  EXCLUDE_WEEKENDS_PARAM,
  type ParamExpressionSpec,
} from "@delpi/tv-dashboard-presentation";

import type { DataParamSchema } from "./dataParamSchema";
import {
  DATE_RANGE_PRESET_PARAM,
  PERIOD_DAYS_PARAM,
  findDateRangeKeys,
  isDateRangePairKey,
} from "./dateRangePresets";
import { isParamExpressionValue } from "./paramExpressions";

/** Valor de update do editor: string parseada pelo schema ou ExpressionSpec intacto. */
export type DataParamUpdateValue = string | ParamExpressionSpec;

const MIN_SANE_YEAR = 1990;
const MAX_SANE_YEAR = 2100;

function isSaneIsoDate(raw: string): boolean {
  const text = raw.trim();
  if (!/^\d{4}-\d{2}-\d{2}/.test(text)) return false;
  const year = Number(text.slice(0, 4));
  if (!Number.isFinite(year) || year < MIN_SANE_YEAR || year > MAX_SANE_YEAR) return false;
  const parsed = new Date(`${text.slice(0, 10)}T00:00:00Z`);
  return !Number.isNaN(parsed.getTime());
}

/** Converte raw de UI (string) para valor tipado do schema. */
export function parseDataParamRaw(
  key: string,
  raw: string,
  schema: DataParamSchema | undefined,
): string | number | boolean | undefined {
  const fieldType = schema?.[key]?.type;
  if (!raw.trim()) return undefined;
  const datePair = findDateRangeKeys(Object.keys(schema ?? {}));
  const looksLikeDate =
    fieldType === "string" &&
    (isDateRangePairKey(key, datePair) ||
      String((schema?.[key] as { format?: string } | undefined)?.format || "").toLowerCase() ===
        "date");
  if (looksLikeDate || /^\d{4}-\d{2}-\d{2}/.test(raw.trim())) {
    if (!isSaneIsoDate(raw)) return undefined;
    return raw.trim().slice(0, 10);
  }
  if (fieldType === "integer" || fieldType === "number") return Number(raw);
  if (fieldType === "boolean" || key === EXCLUDE_WEEKENDS_PARAM) return raw === "true";
  return raw.trim();
}

/**
 * Aplica várias chaves de parâmetro de uma vez (evita race com binding stale
 * quando Período + competence / datas mudam juntos).
 * ExpressionSpec passa intacto — parse de scalars continua via schema.
 */
type ParamPatchContext = {
  /** Schema visível do editor (visibleParamSchema já aplicado). */
  schema?: DataParamSchema;
  /** Valores atuais — necessários para saber se há preset ativo. */
  values?: Record<string, unknown> | undefined;
};

/**
 * Updates de UM param com a regra de conflito de período:
 * expressão/data explícita no par nunca coexiste com `dateRangePreset`
 * relativo, e `competence` (mês fechado SI) força preset `custom`.
 * Compartilhado por DataParamFields e pelo drawer de expressão — mesma regra.
 */
export function buildParamValueUpdates(
  key: string,
  value: DataParamUpdateValue,
  context: ParamPatchContext = {},
): Record<string, DataParamUpdateValue> {
  const schema = context.schema ?? {};
  const activeDatePair = findDateRangeKeys(Object.keys(schema));
  const preset = String(context.values?.[DATE_RANGE_PRESET_PARAM] ?? "").trim();
  const updates: Record<string, DataParamUpdateValue> = { [key]: value };
  if (key === "competence" && typeof value === "string" && value.trim() && activeDatePair) {
    updates[DATE_RANGE_PRESET_PARAM] = "custom";
  }
  if (activeDatePair && isDateRangePairKey(key, activeDatePair)) {
    if (isParamExpressionValue(value)) {
      updates[DATE_RANGE_PRESET_PARAM] = "";
    } else if (preset && preset !== "custom") {
      updates[DATE_RANGE_PRESET_PARAM] = "custom";
    }
  }
  return updates;
}

/**
 * Updates de `dateRangePreset` — preset relativo limpa datas fixas do par,
 * `periodDays` (fora de last_n_days) e `competence` quando aplicável.
 */
export function buildDateRangePresetUpdates(
  value: string,
  context: ParamPatchContext = {},
): Record<string, string> {
  const schema = context.schema ?? {};
  const activeDatePair = findDateRangeKeys(Object.keys(schema));
  const hasCompetence = "competence" in schema;
  const updates: Record<string, string> = { [DATE_RANGE_PRESET_PARAM]: value };
  if (hasCompetence && value && value !== "custom") {
    updates.competence = "";
  }
  if (activeDatePair && value !== "custom") {
    updates[activeDatePair.startKey] = "";
    updates[activeDatePair.endKey] = "";
    if (value !== "last_n_days") {
      updates[PERIOD_DAYS_PARAM] = "";
    }
  }
  return updates;
}

export function applyDataParamRawUpdates(
  current:
    | Record<string, string | number | boolean | null | ParamExpressionSpec | undefined>
    | undefined,
  updates: Record<string, DataParamUpdateValue>,
  schema: DataParamSchema | undefined,
): Record<string, string | number | boolean | ParamExpressionSpec> {
  const next: Record<string, string | number | boolean | ParamExpressionSpec> = {};
  for (const [key, value] of Object.entries(current ?? {})) {
    if (value != null) next[key] = value;
  }
  for (const [key, raw] of Object.entries(updates)) {
    if (isParamExpressionValue(raw)) {
      next[key] = raw;
      continue;
    }
    const parsed = parseDataParamRaw(key, String(raw), schema);
    if (parsed === undefined) delete next[key];
    else next[key] = parsed;
  }
  return next;
}
