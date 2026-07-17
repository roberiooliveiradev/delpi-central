import { mergeDataFilters } from "./comunicadoHelpers";
import type { ComunicadoDataBinding, ComunicadoDataFilters, ComunicadoDataSourceBlock } from "./comunicadoTypes";
import { resolveDataSourceLabel } from "./comunicadoDataArchitecture";

/** Presets de período — espelha labels do MFE (dateRangePresets). */
export const DATA_SOURCE_DATE_RANGE_PRESET_LABELS: Record<string, string> = {
  this_month: "Este mês (até hoje)",
  this_week: "Esta semana (até hoje)",
  this_quarter: "Este trimestre (até hoje)",
  this_year: "Este ano (até hoje)",
  today: "Hoje",
  previous_week: "Semana passada",
  previous_month: "Mês passado",
  previous_quarter: "Trimestre passado",
  previous_year: "Ano passado",
  last_7_days: "Últimos 7 dias",
  last_30_days: "Últimos 30 dias",
  last_90_days: "Últimos 90 dias",
  last_n_days: "Últimos N dias",
  custom: "Personalizado (datas fixas)",
};

/** Rótulos mínimos para o cartão no palco (UI completa fica no catálogo do MFE). */
export const DATA_SOURCE_PARAM_LABELS: Record<string, string> = {
  branch: "Filial",
  filial: "Filial",
  branches: "Filiais",
  dateRangePreset: "Período",
  periodDays: "Dias",
  date_start: "Data início",
  date_end: "Data fim",
  start_date: "Data início",
  end_date: "Data fim",
  date_from: "Data início",
  date_to: "Data fim",
  dataInicio: "Data início",
  dataFim: "Data fim",
  work_center: "Centro de trabalho",
  cost_center: "Centro de custo",
  granularity: "Granularidade",
  group_by: "Agrupar por",
  limit: "Limite",
};

const DATE_START_KEYS = new Set([
  "date_start",
  "start_date",
  "date_from",
  "dataInicio",
  "data_inicial",
  "issue_date_start",
  "modified_from",
  "from",
]);

const DATE_END_KEYS = new Set([
  "date_end",
  "end_date",
  "date_to",
  "dataFim",
  "data_final",
  "issue_date_end",
  "modified_to",
  "to",
]);

const DATE_RANGE_PRESET_PARAM = "dateRangePreset";
const PERIOD_DAYS_PARAM = "periodDays";

export type FormatDataSourceBindingSummaryOptions = {
  slideFilters?: ComunicadoDataFilters | null;
  /** Sobrescreve rótulo da chave (ex.: catálogo completo do MFE). */
  labelForKey?: (key: string) => string;
  /** Humaniza valor (enums, presets). */
  labelForValue?: (key: string, value: string) => string;
  maxFilterLines?: number;
};

export type DataSourceBindingSummary = {
  label: string;
  operationId: string;
  filterLines: string[];
  /** Texto único p/ title/aria. */
  title: string;
};

function isPresent(value: unknown): boolean {
  return value !== null && value !== undefined && String(value).trim() !== "";
}

function defaultLabelForKey(key: string): string {
  return DATA_SOURCE_PARAM_LABELS[key] ?? key.replace(/_/g, " ");
}

function defaultLabelForValue(key: string, value: string): string {
  if (key === DATE_RANGE_PRESET_PARAM) {
    return DATA_SOURCE_DATE_RANGE_PRESET_LABELS[value] ?? value;
  }
  if (value === "true") return "Sim";
  if (value === "false") return "Não";
  return value;
}

function formatFilterLine(
  key: string,
  value: string,
  inherited: boolean,
  options?: FormatDataSourceBindingSummaryOptions,
): string {
  const fromResolver = options?.labelForKey?.(key)?.trim();
  const label =
    fromResolver && fromResolver !== key ? fromResolver : defaultLabelForKey(key);
  const display = options?.labelForValue?.(key, value) ?? defaultLabelForValue(key, value);
  const suffix = inherited ? " (slide)" : "";
  return `${label}: ${display}${suffix}`;
}

/**
 * Linhas de filtro efetivas (slide ∪ bloco) para o cartão da fonte no editor.
 * Preset relativo omite datas cruas; `custom` mantém início/fim.
 */
export function formatDataSourceFilterLines(
  binding: Pick<ComunicadoDataBinding, "params">,
  options?: FormatDataSourceBindingSummaryOptions,
): string[] {
  const blockParams = binding.params ?? {};
  const slide = options?.slideFilters ?? {};
  const merged = mergeDataFilters(slide, blockParams);
  const maxLines = Math.max(1, options?.maxFilterLines ?? 8);
  const lines: string[] = [];
  const skip = new Set<string>();

  const preset = String(merged[DATE_RANGE_PRESET_PARAM] ?? "").trim();
  if (preset && preset !== "custom") {
    lines.push(
      formatFilterLine(
        DATE_RANGE_PRESET_PARAM,
        preset,
        !(DATE_RANGE_PRESET_PARAM in blockParams) && DATE_RANGE_PRESET_PARAM in slide,
        options,
      ),
    );
    skip.add(DATE_RANGE_PRESET_PARAM);
    for (const key of DATE_START_KEYS) skip.add(key);
    for (const key of DATE_END_KEYS) skip.add(key);
    if (preset === "last_n_days" && isPresent(merged[PERIOD_DAYS_PARAM])) {
      lines.push(
        formatFilterLine(
          PERIOD_DAYS_PARAM,
          String(merged[PERIOD_DAYS_PARAM]),
          !(PERIOD_DAYS_PARAM in blockParams) && PERIOD_DAYS_PARAM in slide,
          options,
        ),
      );
      skip.add(PERIOD_DAYS_PARAM);
    } else {
      skip.add(PERIOD_DAYS_PARAM);
    }
  }

  const keys = Object.keys(merged).sort((a, b) => a.localeCompare(b, "pt-BR"));
  for (const key of keys) {
    if (skip.has(key)) continue;
    if (!isPresent(merged[key])) continue;
    const inherited = !(key in blockParams) && key in slide;
    lines.push(formatFilterLine(key, String(merged[key]), inherited, options));
    if (lines.length >= maxLines) break;
  }

  return lines;
}

export function formatDataSourceBindingSummary(
  block: ComunicadoDataSourceBlock,
  options?: FormatDataSourceBindingSummaryOptions,
): DataSourceBindingSummary {
  const label = resolveDataSourceLabel(block);
  const operationId = String(block.dataBinding.operationId ?? "").trim();
  const filterLines = formatDataSourceFilterLines(block.dataBinding, options);
  const titleParts = [label];
  if (operationId && operationId !== label) titleParts.push(operationId);
  if (filterLines.length) titleParts.push(filterLines.join(" · "));
  return {
    label,
    operationId,
    filterLines,
    title: titleParts.join(" — "),
  };
}
