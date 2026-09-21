import {
  resolveEffectivePeriodPreset,
  resolvePeriodPreset,
  type PeriodPresetId,
} from "@delpi/plugin-ui/index";

export type DashboardPeriodDates = {
  dataInicial: string;
  dataFinal: string;
  competence: string;
};

export function defaultDashboardPeriod(now?: Date): DashboardPeriodDates & {
  periodPreset: PeriodPresetId;
} {
  const range = resolvePeriodPreset("this_month", now);
  return {
    dataInicial: range?.dateStart ?? "",
    dataFinal: range?.dateEnd ?? "",
    competence: range?.competence ?? "",
    periodPreset: "this_month",
  };
}

export function applyDashboardPeriodPreset(
  preset: PeriodPresetId,
  current: DashboardPeriodDates,
  now?: Date,
): DashboardPeriodDates & {
  storedPreset: PeriodPresetId | null;
  forceCustom: boolean;
} {
  if (preset === "custom") {
    return { ...current, storedPreset: null, forceCustom: true };
  }
  const range = resolvePeriodPreset(preset, now);
  if (!range) {
    return { ...current, storedPreset: null, forceCustom: true };
  }
  return {
    dataInicial: range.dateStart,
    dataFinal: range.dateEnd,
    competence: range.competence,
    storedPreset: preset,
    forceCustom: false,
  };
}

export function effectiveDashboardPeriodPreset(
  dates: DashboardPeriodDates,
  stored: PeriodPresetId | null | undefined,
  forceCustom: boolean,
  now?: Date,
): PeriodPresetId {
  if (forceCustom) return "custom";
  return resolveEffectivePeriodPreset(dates.dataInicial, dates.dataFinal, stored, now);
}
