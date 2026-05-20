import type { ChartGranularity } from "../types/chart";
import { dateToMonthKey, parseDateParts } from "./dates";
import { buildPeriodBuckets, type PeriodBucket } from "./periodBuckets";

export type TimeSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  value: number;
  registros: number;
};

function dateToDayKey(value: string | null | undefined): string | null {
  const parts = parseDateParts(value);
  if (!parts) return null;

  const month = String(parts.month).padStart(2, "0");
  const day = String(parts.day).padStart(2, "0");
  return `${parts.year}-${month}-${day}`;
}

function dateToWeekKey(value: string | null | undefined): string | null {
  const parts = parseDateParts(value);
  if (!parts) return null;

  const date = new Date(parts.year, parts.month - 1, parts.day);
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  date.setDate(date.getDate() + diff);

  const month = String(date.getMonth() + 1).padStart(2, "0");
  const dayOfMonth = String(date.getDate()).padStart(2, "0");
  return `${date.getFullYear()}-${month}-${dayOfMonth}`;
}

function dateToYearKey(value: string | null | undefined): string | null {
  const parts = parseDateParts(value);
  if (!parts) return null;
  return String(parts.year);
}

function dateToBucketKey(
  value: string | null | undefined,
  granularity: ChartGranularity
): string | null {
  switch (granularity) {
    case "day":
      return dateToDayKey(value);
    case "week":
      return dateToWeekKey(value);
    case "month":
      return dateToMonthKey(value);
    case "year":
      return dateToYearKey(value);
    default:
      return null;
  }
}

export function aggregateQuantityByPeriod<T>({
  items,
  getDate,
  getQuantity,
  dateStart,
  dateEnd,
  granularity,
}: {
  items: T[];
  getDate: (item: T) => string | null | undefined;
  getQuantity: (item: T) => number | null | undefined;
  dateStart?: string;
  dateEnd?: string;
  granularity: ChartGranularity;
}): TimeSeriesPoint[] {
  const { buckets } = buildPeriodBuckets(dateStart, dateEnd, granularity);
  const labelByKey = new Map<string, string>(
    buckets.map((bucket: PeriodBucket) => [bucket.key, bucket.label])
  );

  const totals = new Map<string, { value: number; registros: number }>();

  for (const item of items) {
    const bucketKey = dateToBucketKey(getDate(item), granularity);
    if (!bucketKey || !labelByKey.has(bucketKey)) continue;

    const current = totals.get(bucketKey) ?? { value: 0, registros: 0 };
    current.value += getQuantity(item) ?? 0;
    current.registros += 1;
    totals.set(bucketKey, current);
  }

  return buckets.map((bucket) => {
    const aggregate = totals.get(bucket.key);
    return {
      periodo: bucket.label,
      sortKey: bucket.key,
      dateStart: bucket.date_start,
      dateEnd: bucket.date_end,
      value: Number((aggregate?.value ?? 0).toFixed(2)),
      registros: aggregate?.registros ?? 0,
    };
  });
}

export function aggregateCountByPeriod<T>(
  params: Omit<
    Parameters<typeof aggregateQuantityByPeriod<T>>[0],
    "getQuantity"
  >
): TimeSeriesPoint[] {
  return aggregateQuantityByPeriod({
    ...params,
    getQuantity: () => 1,
  });
}

export function aggregateAverageByPeriod<T>({
  items,
  getDate,
  getValue,
  dateStart,
  dateEnd,
  granularity,
}: {
  items: T[];
  getDate: (item: T) => string | null | undefined;
  getValue: (item: T) => number | null | undefined;
  dateStart?: string;
  dateEnd?: string;
  granularity: ChartGranularity;
}): TimeSeriesPoint[] {
  const { buckets } = buildPeriodBuckets(dateStart, dateEnd, granularity);
  const labelByKey = new Map(buckets.map((bucket) => [bucket.key, bucket.label]));

  const totals = new Map<string, { total: number; count: number }>();

  for (const item of items) {
    const bucketKey = dateToBucketKey(getDate(item), granularity);
    if (!bucketKey || !labelByKey.has(bucketKey)) continue;

    const current = totals.get(bucketKey) ?? { total: 0, count: 0 };
    current.total += getValue(item) ?? 0;
    current.count += 1;
    totals.set(bucketKey, current);
  }

  return buckets.map((bucket) => {
    const aggregate = totals.get(bucket.key);
    const average =
      aggregate && aggregate.count > 0
        ? aggregate.total / aggregate.count
        : 0;

    return {
      periodo: bucket.label,
      sortKey: bucket.key,
      dateStart: bucket.date_start,
      dateEnd: bucket.date_end,
      value: Number(average.toFixed(2)),
      registros: aggregate?.count ?? 0,
    };
  });
}

export function aggregateSumByPeriod<T>(
  params: Parameters<typeof aggregateQuantityByPeriod<T>>[0]
): TimeSeriesPoint[] {
  return aggregateQuantityByPeriod(params);
}
