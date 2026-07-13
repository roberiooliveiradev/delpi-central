/** Presets relativos de período — resolvidos de novo a cada refresh na API. */

export const DATE_RANGE_PRESET_PARAM = "dateRangePreset";
export const PERIOD_DAYS_PARAM = "periodDays";

export type DateRangePresetId =
  | "this_month"
  | "this_week"
  | "today"
  | "last_7_days"
  | "last_30_days"
  | "last_n_days"
  | "custom";

export const DATE_RANGE_PRESET_OPTIONS: Array<{ value: DateRangePresetId; label: string }> = [
  { value: "this_month", label: "Este mês (até hoje)" },
  { value: "this_week", label: "Esta semana (até hoje)" },
  { value: "today", label: "Hoje" },
  { value: "last_7_days", label: "Últimos 7 dias" },
  { value: "last_30_days", label: "Últimos 30 dias" },
  { value: "last_n_days", label: "Últimos N dias" },
  { value: "custom", label: "Personalizado (datas fixas)" },
];

const START_KEYS = [
  "date_start",
  "start_date",
  "date_from",
  "dataInicio",
  "data_inicial",
  "issue_date_start",
  "modified_from",
  "from",
] as const;

const END_KEYS = [
  "date_end",
  "end_date",
  "date_to",
  "dataFim",
  "data_final",
  "issue_date_end",
  "modified_to",
  "to",
] as const;

export type DateRangeKeyPair = { startKey: string; endKey: string };

export function findDateRangeKeys(schemaKeys: Iterable<string>): DateRangeKeyPair | null {
  const set = new Set(schemaKeys);
  const startKey = START_KEYS.find((key) => set.has(key));
  const endKey = END_KEYS.find((key) => set.has(key));
  if (startKey && endKey) return { startKey, endKey };
  return null;
}

export function isDateRangePairKey(key: string, pair: DateRangeKeyPair | null): boolean {
  if (!pair) return false;
  return key === pair.startKey || key === pair.endKey;
}

export function defaultDateRangePreset(pair: DateRangeKeyPair | null): DateRangePresetId | null {
  return pair ? "this_month" : null;
}
