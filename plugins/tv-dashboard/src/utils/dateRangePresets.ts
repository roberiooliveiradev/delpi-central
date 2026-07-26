/** Presets relativos de período — resolvidos de novo a cada refresh na API. */

export const DATE_RANGE_PRESET_PARAM = "dateRangePreset";
export const PERIOD_DAYS_PARAM = "periodDays";

export type DateRangePresetId =
  | "this_month"
  | "this_week"
  | "this_quarter"
  | "this_year"
  | "today"
  | "previous_week"
  | "previous_month"
  | "previous_quarter"
  | "previous_year"
  | "last_7_days"
  | "last_30_days"
  | "last_90_days"
  | "last_n_days"
  | "custom";

export const DATE_RANGE_PRESET_OPTIONS: Array<{ value: DateRangePresetId; label: string }> = [
  { value: "today", label: "Hoje" },
  { value: "this_week", label: "Esta semana (até hoje)" },
  { value: "this_month", label: "Este mês (até hoje)" },
  { value: "this_quarter", label: "Este trimestre (até hoje)" },
  { value: "this_year", label: "Este ano (até hoje)" },
  { value: "previous_week", label: "Semana passada" },
  { value: "previous_month", label: "Mês passado" },
  { value: "previous_quarter", label: "Trimestre passado" },
  { value: "previous_year", label: "Ano passado" },
  { value: "last_7_days", label: "Últimos 7 dias" },
  { value: "last_30_days", label: "Últimos 30 dias" },
  { value: "last_90_days", label: "Últimos 90 dias" },
  { value: "last_n_days", label: "Últimos N dias" },
  { value: "custom", label: "Personalizado (datas fixas)" },
];

/** Pares canônicos — ordem = preferência (start_date HTTP primeiro). */
const DATE_RANGE_KEY_PAIRS: ReadonlyArray<readonly [string, string]> = [
  ["start_date", "end_date"],
  ["date_start", "date_end"],
  ["date_from", "date_to"],
  ["dataInicio", "dataFim"],
  ["data_inicio", "data_fim"],
  ["data_inicial", "data_final"],
  ["issue_date_start", "issue_date_end"],
  ["modified_from", "modified_to"],
  ["from", "to"],
];

export type DateRangeKeyPair = { startKey: string; endKey: string };

export function findDateRangeKeys(schemaKeys: Iterable<string>): DateRangeKeyPair | null {
  const set = new Set(schemaKeys);
  for (const [startKey, endKey] of DATE_RANGE_KEY_PAIRS) {
    if (set.has(startKey) && set.has(endKey)) {
      return { startKey, endKey };
    }
  }
  return null;
}

export function isDateRangePairKey(key: string, pair: DateRangeKeyPair | null): boolean {
  if (!pair) return false;
  return key === pair.startKey || key === pair.endKey;
}

export function defaultDateRangePreset(pair: DateRangeKeyPair | null): DateRangePresetId | null {
  return pair ? "this_month" : null;
}
