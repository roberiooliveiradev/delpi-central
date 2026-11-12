/**
 * GLPI #1197 — quick windows for stock with no effective utilization.
 * The shared period preset starts on the first of the month; this
 * indicator requires exactly 6/12 rolling months, as in its API.
 */
import {
  getRollingMonthsAgoInputValue,
  getTodayInputValue,
} from "./dates";

export type NonMovingWindowPreset =
  | "last_6_months"
  | "last_12_months"
  | "custom";

export const NON_MOVING_WINDOW_PRESET_OPTIONS = [
  { value: "last_6_months", label: "Últimos 6 meses" },
  { value: "last_12_months", label: "Últimos 12 meses" },
] as const;

export function getNonMovingWindowDates(
  preset: Exclude<NonMovingWindowPreset, "custom">,
  reference: Date = new Date(),
): { dateStart: string; dateEnd: string } {
  const months = preset === "last_6_months" ? 6 : 12;
  return {
    dateStart: getRollingMonthsAgoInputValue(months, reference),
    dateEnd: getTodayInputValue(reference),
  };
}

export function detectNonMovingWindowPreset(
  dateStart: string,
  dateEnd: string,
  reference: Date = new Date(),
): NonMovingWindowPreset {
  if (dateEnd !== getTodayInputValue(reference)) return "custom";
  if (dateStart === getRollingMonthsAgoInputValue(6, reference)) {
    return "last_6_months";
  }
  if (dateStart === getRollingMonthsAgoInputValue(12, reference)) {
    return "last_12_months";
  }
  return "custom";
}
