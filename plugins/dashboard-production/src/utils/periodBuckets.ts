import type { ChartGranularity } from "../types/chart";
import { monthKeyToLabel } from "./dates";

export type PeriodBucket = {
  key: string;
  label: string;
  start_date: string;
  end_date: string;
};

export const MAX_PERIOD_BUCKETS = 60;

export type BuildPeriodBucketsResult = {
  buckets: PeriodBucket[];
  truncated: boolean;
};

function parseIsoDate(value: string): Date | null {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!match) return null;

  const year = Number(match[1]);
  const month = Number(match[2]);
  const day = Number(match[3]);
  const date = new Date(year, month - 1, day);

  if (
    date.getFullYear() !== year ||
    date.getMonth() !== month - 1 ||
    date.getDate() !== day
  ) {
    return null;
  }

  return date;
}

function toIsoDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function addDays(date: Date, days: number): Date {
  const next = new Date(date);
  next.setDate(next.getDate() + days);
  return next;
}

function startOfWeekMonday(date: Date): Date {
  const day = date.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  return addDays(date, diff);
}

function endOfMonth(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth() + 1, 0);
}

function clampRange(
  bucketStart: Date,
  bucketEnd: Date,
  rangeStart: Date,
  rangeEnd: Date
): { start: Date; end: Date } | null {
  const start = bucketStart < rangeStart ? rangeStart : bucketStart;
  const end = bucketEnd > rangeEnd ? rangeEnd : bucketEnd;

  if (start > end) return null;

  return { start, end };
}

function formatDayLabel(iso: string): string {
  const [year, month, day] = iso.split("-");
  return `${day}/${month}/${year.slice(2)}`;
}

function formatWeekLabel(startIso: string, endIso: string): string {
  const start = formatDayLabel(startIso);
  const end = formatDayLabel(endIso);
  return start === end ? start : `${start} – ${end}`;
}

function pushBucket(
  buckets: PeriodBucket[],
  key: string,
  label: string,
  start: Date,
  end: Date
): void {
  buckets.push({
    key,
    label,
    start_date: toIsoDate(start),
    end_date: toIsoDate(end),
  });
}

export function suggestGranularity(
  dateStart?: string,
  dateEnd?: string
): ChartGranularity {
  if (!dateStart || !dateEnd) return "month";

  const start = parseIsoDate(dateStart);
  const end = parseIsoDate(dateEnd);

  if (!start || !end || start > end) return "month";

  const diffDays =
    Math.floor((end.getTime() - start.getTime()) / 86_400_000) + 1;

  if (diffDays <= 31) return "day";
  if (diffDays <= 120) return "week";
  if (diffDays <= 730) return "month";
  return "year";
}

export function buildPeriodBuckets(
  dateStart: string | undefined,
  dateEnd: string | undefined,
  granularity: ChartGranularity
): BuildPeriodBucketsResult {
  if (!dateStart || !dateEnd) {
    return { buckets: [], truncated: false };
  }

  const rangeStart = parseIsoDate(dateStart);
  const rangeEnd = parseIsoDate(dateEnd);

  if (!rangeStart || !rangeEnd || rangeStart > rangeEnd) {
    return { buckets: [], truncated: false };
  }

  const buckets: PeriodBucket[] = [];

  if (granularity === "day") {
    let cursor = new Date(rangeStart);

    while (cursor <= rangeEnd) {
      pushBucket(
        buckets,
        toIsoDate(cursor),
        formatDayLabel(toIsoDate(cursor)),
        cursor,
        cursor
      );
      cursor = addDays(cursor, 1);
    }
  }

  if (granularity === "week") {
    let cursor = startOfWeekMonday(rangeStart);

    while (cursor <= rangeEnd) {
      const bucketEnd = addDays(cursor, 6);
      const clamped = clampRange(cursor, bucketEnd, rangeStart, rangeEnd);

      if (clamped) {
        const startIso = toIsoDate(clamped.start);
        const endIso = toIsoDate(clamped.end);
        pushBucket(
          buckets,
          startIso,
          formatWeekLabel(startIso, endIso),
          clamped.start,
          clamped.end
        );
      }

      cursor = addDays(cursor, 7);
    }
  }

  if (granularity === "month") {
    let cursor = new Date(rangeStart.getFullYear(), rangeStart.getMonth(), 1);

    while (cursor <= rangeEnd) {
      const monthEnd = endOfMonth(cursor);
      const clamped = clampRange(cursor, monthEnd, rangeStart, rangeEnd);

      if (clamped) {
        const monthKey = `${clamped.start.getFullYear()}-${String(
          clamped.start.getMonth() + 1
        ).padStart(2, "0")}`;

        pushBucket(
          buckets,
          monthKey,
          monthKeyToLabel(monthKey),
          clamped.start,
          clamped.end
        );
      }

      cursor = new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
    }
  }

  if (granularity === "year") {
    let year = rangeStart.getFullYear();
    const lastYear = rangeEnd.getFullYear();

    while (year <= lastYear) {
      const yearStart = new Date(year, 0, 1);
      const yearEnd = new Date(year, 11, 31);
      const clamped = clampRange(yearStart, yearEnd, rangeStart, rangeEnd);

      if (clamped) {
        pushBucket(
          buckets,
          String(year),
          String(year),
          clamped.start,
          clamped.end
        );
      }

      year += 1;
    }
  }

  if (buckets.length <= MAX_PERIOD_BUCKETS) {
    return { buckets, truncated: false };
  }

  return {
    buckets: buckets.slice(0, MAX_PERIOD_BUCKETS),
    truncated: true,
  };
}
