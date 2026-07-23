import type { LmpDashboardItem, LmpListingKind } from "../types/lmp";
import { formatLmpApiDateDisplay, lmpDateSortKey } from "./dates";

export function formatLmpApiDate(value?: string | null): string {
  return formatLmpApiDateDisplay(value);
}

export function formatListingKind(kind?: LmpListingKind | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "—";
}

export function parseLmpDateNumber(value?: string | null): number {
  const key = lmpDateSortKey(value);
  if (!key) return 0;
  const parsed = Number(key);
  return Number.isNaN(parsed) ? 0 : parsed;
}

export function formatDashboardRevision(
  row: Pick<LmpDashboardItem, "homolog_revision" | "measurement_revision">,
): string {
  const revision =
    row.homolog_revision?.trim() || row.measurement_revision?.trim();
  return revision || "—";
}

export function formatCycleIndex(value?: number | null): string {
  if (value == null || value < 1) return "1";
  return String(value);
}

export function buildLmpDashboardRowKey(row: LmpDashboardItem): string {
  const revision =
    row.homolog_revision?.trim() ||
    row.measurement_revision?.trim() ||
    "sem-revisao";
  const cycle = row.cycle_index != null && row.cycle_index > 0 ? row.cycle_index : 1;
  return `${row.branch ?? "sem-filial"}-${row.listing_kind ?? "sem-tipo"}-${row.sale_number}-${revision}-${cycle}`;
}
