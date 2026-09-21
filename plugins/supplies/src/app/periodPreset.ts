/**
 * Supplies period presets — shared temporal contract from @delpi/plugin-ui.
 * Field names stay `from`/`to` for existing Overview/PR/PO consumers.
 * KPI chip (MTD/YTD) stays portal-local.
 */

import {
  PERIOD_PRESET_IDS,
  PERIOD_PRESET_OPTIONS,
  detectPeriodPreset,
  parsePeriodPresetId as parseSharedPeriodPresetId,
  resolvePeriodPreset as resolveSharedPeriodPreset,
  todayIsoInTimeZone,
  type PeriodPresetId,
} from "@delpi/plugin-ui/index";

export { PERIOD_PRESET_IDS, PERIOD_PRESET_OPTIONS, todayIsoInTimeZone };
export type { PeriodPresetId };

export type PeriodPresetRange = {
  from: string;
  to: string;
};

export function resolvePeriodPreset(
  preset: PeriodPresetId,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetRange | null {
  const range = resolveSharedPeriodPreset(preset, now, timeZone);
  if (!range) return null;
  return { from: range.dateStart, to: range.dateEnd };
}

/**
 * Returns which preset id matches the inclusive [from, to] range, or `"custom"`.
 * Used by PR/PO filters on F5 (dates in URL; no dedicated period query param).
 */
export function matchPeriodPreset(
  from: string,
  to: string,
  now: Date = new Date(),
  timeZone = "America/Sao_Paulo",
): PeriodPresetId {
  const fromTrim = (from || "").trim();
  const toTrim = (to || "").trim();
  if (!fromTrim || !toTrim) return "custom";
  return detectPeriodPreset(fromTrim, toTrim, now, timeZone);
}

export function parsePeriodPresetId(raw: string | null | undefined): PeriodPresetId | null {
  if (!raw) return null;
  if ((PERIOD_PRESET_IDS as readonly string[]).includes(raw)) {
    return raw as PeriodPresetId;
  }
  return parseSharedPeriodPresetId(raw);
}

/** MTD/YTD chip for DashboardKpiCard — mirrors Commercial resolvePeriodKindChip. */
export type PeriodKindChip = "MTD" | "YTD";

export function resolvePeriodKindChip(
  preset: PeriodPresetId | null | undefined,
): PeriodKindChip | null {
  if (preset === "today" || preset === "this_week" || preset === "this_month" || preset === "last_month") {
    return "MTD";
  }
  if (preset === "this_year" || preset === "last_12_months") return "YTD";
  return null;
}
