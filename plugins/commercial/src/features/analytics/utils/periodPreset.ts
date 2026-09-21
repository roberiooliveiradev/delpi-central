/**
 * Commercial period presets — shared temporal contract from @delpi/plugin-ui.
 * KPI chip (MTD/YTD) stays portal-local.
 */

export {
  PERIOD_PRESET_IDS,
  PERIOD_PRESET_OPTIONS,
  detectPeriodPreset,
  parsePeriodPresetId,
  resolveEffectivePeriodPreset,
  resolvePeriodPreset,
  todayIsoInTimeZone,
  type PeriodPresetId,
  type PeriodPresetRange,
  type ResolvedPeriodPresetId,
} from "@delpi/plugin-ui/index";

export { resolvePeriodKindChip, type PeriodKindChip } from "./periodKindChip";
