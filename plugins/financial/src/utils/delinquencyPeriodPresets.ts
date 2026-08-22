import { formatIsoDate, parseIsoDate } from "./delinquencyPeriod";

export const DELINQUENCY_PERIOD_PRESET_IDS = [
  "this_month",
  "this_semester",
  "this_year",
] as const;

export type DelinquencyPeriodPreset = (typeof DELINQUENCY_PERIOD_PRESET_IDS)[number];

export type DelinquencyPeriodRange = {
  startDate: string;
  endDate: string;
};

function firstDayOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

/** Intervalo inclusivo na UI (De/até). */
export function resolveDelinquencyPeriodPreset(
  preset: DelinquencyPeriodPreset,
  referenceDate = new Date(),
): DelinquencyPeriodRange {
  const today = new Date(
    referenceDate.getFullYear(),
    referenceDate.getMonth(),
    referenceDate.getDate(),
  );
  const year = today.getFullYear();
  const month = today.getMonth();

  switch (preset) {
    case "this_month":
      return {
        startDate: formatIsoDate(firstDayOfMonth(today)),
        endDate: formatIsoDate(today),
      };
    case "this_semester": {
      const semesterStartMonth = month < 6 ? 0 : 6;
      return {
        startDate: formatIsoDate(new Date(year, semesterStartMonth, 1)),
        endDate: formatIsoDate(today),
      };
    }
    case "this_year":
      return {
        startDate: formatIsoDate(new Date(year, 0, 1)),
        endDate: formatIsoDate(today),
      };
    default:
      return resolveDelinquencyPeriodPreset("this_month", referenceDate);
  }
}

export function detectDelinquencyPeriodPreset(
  startDate: string | null,
  endDate: string | null,
  referenceDate = new Date(),
): DelinquencyPeriodPreset | null {
  if (!startDate || !endDate) return null;
  const start = parseIsoDate(startDate);
  const end = parseIsoDate(endDate);
  if (!start || !end) return null;

  for (const preset of DELINQUENCY_PERIOD_PRESET_IDS) {
    const range = resolveDelinquencyPeriodPreset(preset, referenceDate);
    if (range.startDate === startDate && range.endDate === endDate) {
      return preset;
    }
  }
  return null;
}
