import type { ChartGranularity } from "@delpi/plugin-ui/index";

export const BILLING_SERIES_PRESETS = [
  "today",
  "this_week",
  "this_month",
  "this_quarter",
  "this_year",
  "last_12_months",
  "custom",
] as const;

export type BillingSeriesPeriodPreset = (typeof BILLING_SERIES_PRESETS)[number];

export const DEFAULT_BILLING_SERIES_PRESET = "last_12_months" as const;

export const BILLING_SERIES_PRESET_OPTIONS: {
  id: BillingSeriesPeriodPreset;
  label: string;
}[] = [
  { id: "today", label: "Hoje" },
  { id: "this_week", label: "Esta semana" },
  { id: "this_month", label: "Este mês" },
  { id: "this_quarter", label: "Este trimestre" },
  { id: "this_year", label: "Este ano" },
  { id: "last_12_months", label: "Últimos 12 meses" },
  { id: "custom", label: "Personalizado" },
];

export const BILLING_SERIES_GRANULARITY_OPTIONS: {
  value: ChartGranularity;
  label: string;
}[] = [
  { value: "day", label: "Dia" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mês" },
  { value: "year", label: "Ano" },
];

const MAX_SPAN_DAYS: Record<ChartGranularity, number> = {
  day: 93,
  week: 366,
  month: 744,
  year: 3660,
};

export function toIsoDate(value: Date): string {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function startOfDay(value: Date): Date {
  return new Date(value.getFullYear(), value.getMonth(), value.getDate());
}

function startOfWeekMonday(value: Date): Date {
  const start = startOfDay(value);
  const weekday = start.getDay();
  const diff = weekday === 0 ? -6 : 1 - weekday;
  start.setDate(start.getDate() + diff);
  return start;
}

function startOfQuarter(value: Date): Date {
  const month = Math.floor(value.getMonth() / 3) * 3;
  return new Date(value.getFullYear(), month, 1);
}

export function periodRangeFromBillingPreset(
  preset: Exclude<BillingSeriesPeriodPreset, "custom">,
  today: Date = new Date(),
): { startDate: string; endDate: string } {
  const end = startOfDay(today);
  if (preset === "today") {
    return { startDate: toIsoDate(end), endDate: toIsoDate(end) };
  }
  if (preset === "this_week") {
    return { startDate: toIsoDate(startOfWeekMonday(end)), endDate: toIsoDate(end) };
  }
  if (preset === "this_month") {
    return {
      startDate: toIsoDate(new Date(end.getFullYear(), end.getMonth(), 1)),
      endDate: toIsoDate(end),
    };
  }
  if (preset === "this_quarter") {
    return { startDate: toIsoDate(startOfQuarter(end)), endDate: toIsoDate(end) };
  }
  if (preset === "this_year") {
    return {
      startDate: toIsoDate(new Date(end.getFullYear(), 0, 1)),
      endDate: toIsoDate(end),
    };
  }
  const start = new Date(end.getFullYear(), end.getMonth() - 11, 1);
  return { startDate: toIsoDate(start), endDate: toIsoDate(end) };
}

export function inclusiveDayCount(startDate: string, endDate: string): number {
  const start = new Date(`${startDate}T00:00:00`);
  const end = new Date(`${endDate}T00:00:00`);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || start > end) {
    return 0;
  }
  return Math.floor((end.getTime() - start.getTime()) / 86_400_000) + 1;
}

export function allowedBillingSeriesGranularities(
  startDate: string,
  endDate: string,
): ChartGranularity[] {
  const days = inclusiveDayCount(startDate, endDate);
  return (Object.keys(MAX_SPAN_DAYS) as ChartGranularity[]).filter(
    (grain) => days > 0 && days <= MAX_SPAN_DAYS[grain],
  );
}

export function billingSeriesPresetLabel(preset: BillingSeriesPeriodPreset): string {
  return (
    BILLING_SERIES_PRESET_OPTIONS.find((item) => item.id === preset)?.label ??
    "Período"
  );
}
