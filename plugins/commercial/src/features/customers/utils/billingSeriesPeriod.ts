import type { ChartGranularity } from "@delpi/plugin-ui/index";

import {
  PERIOD_PRESET_OPTIONS,
  resolvePeriodPreset,
  type PeriodPresetId,
} from "../../analytics/utils/periodPreset";

export const BILLING_SERIES_PRESETS = [
  "today",
  "this_week",
  "this_month",
  "last_month",
  "this_quarter",
  "this_year",
  "last_12_months",
  "custom",
] as const;

export type BillingSeriesPeriodPreset = (typeof BILLING_SERIES_PRESETS)[number];

export const DEFAULT_BILLING_SERIES_PRESET = "last_12_months" as const;

/** Labels/order aligned with Overview `PERIOD_PRESET_OPTIONS`. */
export const BILLING_SERIES_PRESET_OPTIONS: {
  id: BillingSeriesPeriodPreset;
  label: string;
}[] = PERIOD_PRESET_OPTIONS.map((option) => ({
  id: option.value as BillingSeriesPeriodPreset,
  label: option.label,
}));

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

/**
 * Resolve billing chart range from a shared analytics period preset.
 * Maps `dateStart`/`dateEnd` (Overview) → `startDate`/`endDate` (billing API).
 */
export function periodRangeFromBillingPreset(
  preset: Exclude<BillingSeriesPeriodPreset, "custom">,
  today: Date = new Date(),
): { startDate: string; endDate: string } {
  const range = resolvePeriodPreset(preset as PeriodPresetId, today);
  if (!range) {
    return { startDate: "", endDate: "" };
  }
  return { startDate: range.dateStart, endDate: range.dateEnd };
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
