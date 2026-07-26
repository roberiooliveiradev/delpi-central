import { useCallback } from "react";
import { getPpmSeries } from "../api/qualityApi";
import type { ChartGranularity } from "../types/chart";
import type { DateRangeParams, PpmType } from "../types/ppm";
import { useQualityResource } from "./useQualityResource";

export type PpmSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  ppm: number;
};

type UsePpmChartSeriesParams = {
  type: PpmType;
  filters: DateRangeParams;
  granularity: ChartGranularity;
  enabled?: boolean;
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
  granularity,
  enabled = true,
}: UsePpmChartSeriesParams): UsePpmChartSeriesResult {
  const cacheKey = [
    "ppm-series",
    type,
    granularity,
    filters.branch ?? "",
    filters.start_date ?? "",
    filters.end_date ?? "",
    filters.product_prefix ?? "",
  ].join(":");

  const { data, loading, error, reload } = useQualityResource(
    (signal) =>
      getPpmSeries(
        type,
        {
          branch: filters.branch,
          start_date: filters.start_date,
          end_date: filters.end_date,
          granularity,
          product_prefix: filters.product_prefix,
        },
        signal
      ),
    [
      type,
      granularity,
      filters.branch,
      filters.start_date,
      filters.end_date,
      filters.product_prefix,
    ],
    { cacheKey, cacheTtlMs: 60_000, enabled }
  );

  const points: PpmSeriesPoint[] =
    data?.points.map((point) => ({
      periodo: point.periodo,
      sortKey: point.sort_key,
      dateStart: point.start_date,
      dateEnd: point.end_date,
      ppm: point.ppm,
    })) ?? [];

  const forceReload = useCallback(() => {
    reload();
  }, [reload]);

  return {
    points,
    loading,
    truncated: data?.truncated ?? false,
    error,
    reload: forceReload,
  };
}
