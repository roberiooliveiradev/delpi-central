import type { Audit5s } from "../types/audit5s";
import type { Kaizen } from "../types/kaizen";
import { dateToMonthKey, monthKeyToLabel } from "./dates";

export type ChartDatum = {
  name: string;
  value: number;
};

export function aggregateKaizenByStatus(items: Kaizen[]): ChartDatum[] {
  const buckets = new Map<string, number>();

  for (const item of items) {
    const key = item.status?.trim() || "Sem status";
    buckets.set(key, (buckets.get(key) ?? 0) + 1);
  }

  return [...buckets.entries()]
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value);
}

export function aggregateKaizenSavingsBySector(items: Kaizen[]): ChartDatum[] {
  const buckets = new Map<string, number>();

  for (const item of items) {
    const key = item.sector?.trim() || "Sem setor";
    buckets.set(key, (buckets.get(key) ?? 0) + (item.daily_savings ?? 0));
  }

  return [...buckets.entries()]
    .map(([name, value]) => ({
      name,
      value: Number(value.toFixed(2)),
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);
}

export function aggregateAudit5sByArea(items: Audit5s[]): ChartDatum[] {
  const buckets = new Map<string, { total: number; count: number }>();

  for (const item of items) {
    const key = item.evaluated_area?.trim() || "Sem área";
    const score = item.average_line_score ?? 0;
    const current = buckets.get(key) ?? { total: 0, count: 0 };
    current.total += score;
    current.count += 1;
    buckets.set(key, current);
  }

  return [...buckets.entries()]
    .map(([name, { total, count }]) => ({
      name,
      value: Number((total / count).toFixed(2)),
    }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);
}

export function aggregateAudit5sByMonth(items: Audit5s[]): ChartDatum[] {
  const buckets = new Map<string, { sortKey: string; total: number; count: number }>();

  for (const item of items) {
    const monthKey = dateToMonthKey(item.date);
    if (!monthKey) continue;

    const current = buckets.get(monthKey) ?? {
      sortKey: monthKey,
      total: 0,
      count: 0,
    };
    current.total += item.average_line_score ?? 0;
    current.count += 1;
    buckets.set(monthKey, current);
  }

  return [...buckets.values()]
    .sort((a, b) => a.sortKey.localeCompare(b.sortKey))
    .map((bucket) => ({
      name: monthKeyToLabel(bucket.sortKey),
      value: Number((bucket.total / bucket.count).toFixed(2)),
    }));
}
