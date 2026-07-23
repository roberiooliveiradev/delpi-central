import type { ChartGranularity } from "../types/chart";
import type { Audit5s } from "../types/audit5s";
import type { Kaizen } from "../types/kaizen";
import {
  aggregateAverageByPeriod,
  aggregateCountByPeriod,
  aggregateSumByPeriod,
  type TimeSeriesPoint,
} from "./timeSeriesAggregation";

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

export function aggregateKaizenCountByPeriod(
  items: Kaizen[],
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): TimeSeriesPoint[] {
  return aggregateCountByPeriod({
    items,
    // Mesma âncora do KPI total_kaizens (API: quantity_date).
    getDate: (item) => item.quantity_date ?? item.date_implemented,
    dateStart,
    dateEnd,
    granularity,
  });
}

export function aggregateKaizenSavingsByPeriod(
  items: Kaizen[],
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): TimeSeriesPoint[] {
  return aggregateSumByPeriod({
    items,
    getDate: (item) => item.date_implemented,
    getQuantity: (item) => item.daily_savings,
    dateStart,
    dateEnd,
    granularity,
  });
}

export function aggregateAudit5sScoreByPeriod(
  items: Audit5s[],
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): TimeSeriesPoint[] {
  return aggregateAverageByPeriod({
    items,
    getDate: (item) => item.date,
    getValue: (item) => item.average_line_score,
    dateStart,
    dateEnd,
    granularity,
  });
}

/** @deprecated Use aggregateAudit5sScoreByPeriod com granularidade configurável */
export function aggregateAudit5sByMonth(items: Audit5s[]): ChartDatum[] {
  return aggregateAudit5sScoreByPeriod(
    items,
    undefined,
    undefined,
    "month"
  ).map((point) => ({
    name: point.periodo,
    value: point.value,
  }));
}
