import type { LmpDashboardItem, LmpListingKind } from "../types/lmp";

export function formatLmpApiDate(value?: string | null): string {
  if (!value || value.length !== 8) return "—";
  const year = value.slice(0, 4);
  const month = value.slice(4, 6);
  const day = value.slice(6, 8);
  return `${day}/${month}/${year}`;
}

export function formatListingKind(kind?: LmpListingKind | null): string {
  if (kind === "AMOSTRA") return "Amostra";
  if (kind === "OUTRO") return "Outro";
  if (kind === "LMP") return "LMP";
  return kind ?? "—";
}

export function parseLmpDateNumber(value?: string | null): number {
  if (!value) return 0;
  const normalized = value.replaceAll("-", "");
  if (normalized.length !== 8) return 0;
  const parsed = Number(normalized);
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
