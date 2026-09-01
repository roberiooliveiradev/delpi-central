import type { BillingLine, BillingSeriesPoint, FinancialBranch } from "../types";

export function clampPercent(value: number | null | undefined): number {
  if (typeof value !== "number" || !Number.isFinite(value)) return 0;
  return Math.min(100, Math.max(0, value));
}

export function billingSeriesKeys(branch: FinancialBranch): Array<"rol01" | "rol02"> {
  if (branch === "01") return ["rol01"];
  if (branch === "02") return ["rol02"];
  return ["rol01", "rol02"];
}

export function waterfallPeak(lines: BillingLine[]): number {
  const values = lines.map((line) => Math.abs(line.value)).filter((value) => value > 0);
  return values.length ? Math.max(...values) : 0;
}

export function waterfallBarWidth(value: number, peak: number): number {
  if (!(peak > 0) || !Number.isFinite(value)) return 0;
  const ratio = (Math.abs(value) / peak) * 100;
  if (ratio <= 0) return 0;
  return Math.min(100, Math.max(6, ratio));
}

export function seriesChartRows(items: BillingSeriesPoint[]): Array<Record<string, string | number>> {
  return items.map((point) => ({
    periodo: point.period || point.sortKey,
    rol01: point.rol01,
    rol02: point.rol02,
  }));
}
