import type { ChartGranularity } from "../types/chart";
import type { TransformaMonthlyItem, TransformaProcess } from "../types/engineering";
import { dateToMonthKey } from "./dates";
import { buildPeriodBuckets } from "./periodBuckets";
import { aggregateSumByPeriod } from "./timeSeriesAggregation";

export type OtdMonthlyLike = {
  month?: string | number;
  year?: string | number;
  month_date?: string;
  otd_percentage?: number;
  on_time_lines?: number;
  late_lines?: number;
};

function monthKeyFromItem(item: OtdMonthlyLike): string | null {
  if (item.month_date) return dateToMonthKey(item.month_date);

  if (item.month != null && item.year != null) {
    const month = String(item.month).padStart(2, "0");
    const year = String(item.year);
    return `${year}-${month}`;
  }

  return null;
}

function monthInRange(
  monthKey: string,
  dateStart?: string,
  dateEnd?: string
): boolean {
  const startKey = dateStart ? dateToMonthKey(dateStart) : null;
  const endKey = dateEnd ? dateToMonthKey(dateEnd) : null;
  if (startKey && monthKey < startKey) return false;
  if (endKey && monthKey > endKey) return false;
  return true;
}

export function buildOtdTrendSeries(
  monthly: OtdMonthlyLike[],
  dateStart?: string,
  dateEnd?: string,
  granularity: ChartGranularity = "month"
): Array<{ name: string; otd: number; late: number; onTime: number }> {
  if (granularity === "day" || granularity === "week") {
    return [];
  }

  const byMonth = new Map<
    string,
    { otd: number; late: number; onTime: number; total: number }
  >();

  for (const item of monthly) {
    const key = monthKeyFromItem(item);
    if (!key || !monthInRange(key, dateStart, dateEnd)) continue;

    byMonth.set(key, {
      otd: Number(item.otd_percentage ?? 0),
      late: Number(item.late_lines ?? 0),
      onTime: Number(item.on_time_lines ?? 0),
      total: Number(item.on_time_lines ?? 0) + Number(item.late_lines ?? 0),
    });
  }

  if (granularity === "month") {
    const { buckets } = buildPeriodBuckets(dateStart, dateEnd, "month");
    return buckets.map((bucket) => {
      const row = byMonth.get(bucket.key);
      return {
        name: bucket.label,
        otd: row?.otd ?? 0,
        late: row?.late ?? 0,
        onTime: row?.onTime ?? 0,
      };
    });
  }

  const yearTotals = new Map<
    string,
    { late: number; onTime: number; otdSum: number; weight: number }
  >();

  for (const [monthKey, row] of byMonth) {
    const year = monthKey.slice(0, 4);
    const current = yearTotals.get(year) ?? {
      late: 0,
      onTime: 0,
      otdSum: 0,
      weight: 0,
    };
    const weight = row.total || 1;
    current.late += row.late;
    current.onTime += row.onTime;
    current.otdSum += row.otd * weight;
    current.weight += weight;
    yearTotals.set(year, current);
  }

  const { buckets } = buildPeriodBuckets(dateStart, dateEnd, "year");
  return buckets.map((bucket) => {
    const row = yearTotals.get(bucket.key);
    const total = (row?.onTime ?? 0) + (row?.late ?? 0);
    const otd =
      row && row.weight > 0
        ? row.otdSum / row.weight
        : total > 0
          ? (row!.onTime / total) * 100
          : 0;

    return {
      name: bucket.label,
      otd: Number(otd.toFixed(2)),
      late: row?.late ?? 0,
      onTime: row?.onTime ?? 0,
    };
  });
}

export function buildTransformaSavingsSeries(
  processes: TransformaProcess[],
  monthly: TransformaMonthlyItem[],
  dateStart?: string,
  dateEnd?: string,
  granularity: ChartGranularity = "month"
): Array<{ name: string; net: number }> {
  const datedProcesses = processes.filter((item) => item.implementetion_date);

  if (datedProcesses.length > 0) {
    const points = aggregateSumByPeriod({
      items: datedProcesses,
      getDate: (item) => item.implementetion_date,
      getQuantity: (item) => item.daily_savings ?? 0,
      dateStart,
      dateEnd,
      granularity,
    });

    return points.map((point) => ({
      name: point.periodo,
      net: point.value,
    }));
  }

  if (granularity === "day" || granularity === "week") {
    return [];
  }

  const byMonth = new Map<string, number>();
  for (const item of monthly) {
    const rawMonth = item.month?.trim() ?? "";
    const key =
      rawMonth.length === 7
        ? rawMonth
        : dateToMonthKey(rawMonth.length >= 6 ? `${rawMonth}-01` : rawMonth);
    if (!key || !monthInRange(key, dateStart, dateEnd)) continue;
    byMonth.set(key, Number(item.net_savings_month ?? 0));
  }

  if (granularity === "month") {
    const { buckets } = buildPeriodBuckets(dateStart, dateEnd, "month");
    return buckets.map((bucket) => ({
      name: bucket.label,
      net: byMonth.get(bucket.key) ?? 0,
    }));
  }

  const yearTotals = new Map<string, number>();
  for (const [monthKey, value] of byMonth) {
    const year = monthKey.slice(0, 4);
    yearTotals.set(year, (yearTotals.get(year) ?? 0) + value);
  }

  const { buckets } = buildPeriodBuckets(dateStart, dateEnd, "year");
  return buckets.map((bucket) => ({
    name: bucket.label,
    net: yearTotals.get(bucket.key) ?? 0,
  }));
}
