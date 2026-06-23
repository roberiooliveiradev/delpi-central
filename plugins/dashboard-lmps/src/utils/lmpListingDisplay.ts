import type { LmpDashboardItem } from "../types/lmp";

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
