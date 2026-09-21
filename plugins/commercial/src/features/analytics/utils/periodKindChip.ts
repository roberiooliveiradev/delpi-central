import type { PeriodPresetId } from "@delpi/plugin-ui/index";

/** Chip curto MTD/YTD para cards Overview (ata §5). */
export type PeriodKindChip = "MTD" | "YTD";

export function resolvePeriodKindChip(
  preset: PeriodPresetId | null | undefined,
): PeriodKindChip | null {
  switch (preset) {
    case "this_month":
      return "MTD";
    case "this_year":
    case "last_12_months":
      return "YTD";
    default:
      return null;
  }
}
