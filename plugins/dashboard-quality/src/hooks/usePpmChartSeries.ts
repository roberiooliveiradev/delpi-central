import { useCallback, useEffect, useMemo, useState } from "react";
import { getPpmSummary } from "../api/qualityApi";
import type { ChartGranularity } from "../types/chart";
import type { DateRangeParams, PpmType } from "../types/ppm";
import { buildPeriodBuckets } from "../utils/periodBuckets";

export type PpmSeriesPoint = {
  periodo: string;
  sortKey: string;
  ppm: number;
};

type UsePpmChartSeriesParams = {
  type: PpmType;
  filters: DateRangeParams;
  dateStart?: string;
  dateEnd?: string;
  granularity: ChartGranularity;
};

type UsePpmChartSeriesResult = {
  points: PpmSeriesPoint[];
  loading: boolean;
  truncated: boolean;
  error: string | null;
  reload: () => void;
};

export function usePpmChartSeries({
  type,
  filters,
  dateStart,
  dateEnd,
  granularity,
}: UsePpmChartSeriesParams): UsePpmChartSeriesResult {
  const [points, setPoints] = useState<PpmSeriesPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [truncated, setTruncated] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const { buckets, truncated: isTruncated } = useMemo(
    () => buildPeriodBuckets(dateStart, dateEnd, granularity),
    [dateStart, dateEnd, granularity]
  );

  const stableBranch = filters.branch;

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      if (buckets.length === 0) {
        setPoints([]);
        setTruncated(false);
        setLoading(false);
        setError(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        setTruncated(isTruncated);

        const summaries = await Promise.all(
          buckets.map((bucket) =>
            getPpmSummary(
              type,
              {
                branch: stableBranch,
                date_start: bucket.date_start,
                date_end: bucket.date_end,
              },
              controller.signal
            )
          )
        );

        setPoints(
          buckets.map((bucket, index) => ({
            periodo: bucket.label,
            sortKey: bucket.key,
            ppm: Number(summaries[index]?.ppm ?? 0),
          }))
        );
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar evolução do PPM"
        );
        setPoints([]);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [type, stableBranch, buckets, isTruncated, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    points,
    loading,
    truncated,
    error,
    reload,
  };
}
