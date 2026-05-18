import { useCallback } from "react";
import { getNonconformitySeries } from "../api/qualityApi";
import type { ChartGranularity, ChartSeriesPoint } from "../types/chart";
import type { ListNonconformitiesParams } from "../types/nonconformity";
import { useQualityResource } from "./useQualityResource";

type UseNonconformitiesChartParams = {
  filters: Omit<ListNonconformitiesParams, "page" | "page_size">;
  granularity: ChartGranularity;
};

type UseNonconformitiesChartResult = {
  points: ChartSeriesPoint[];
  loading: boolean;
  truncated: boolean;
  error: string | null;
  reload: () => void;
};

export function useNonconformitiesChart({
  filters,
  granularity,
}: UseNonconformitiesChartParams): UseNonconformitiesChartResult {
  const cacheKey = [
    "nc-series",
    filters.type ?? "all",
    granularity,
    filters.branch ?? "",
    filters.date_start ?? "",
    filters.date_end ?? "",
    filters.status ?? "",
    filters.item_code ?? "",
    filters.description ?? "",
  ].join(":");

  const { data, loading, error, reload } = useQualityResource(
    (signal) =>
      getNonconformitySeries(
        {
          type: filters.type,
          branch: filters.branch,
          date_start: filters.date_start,
          date_end: filters.date_end,
          status: filters.status,
          item_code: filters.item_code,
          description: filters.description,
          granularity,
        },
        signal
      ),
    [
      filters.type,
      granularity,
      filters.branch,
      filters.date_start,
      filters.date_end,
      filters.status,
      filters.item_code,
      filters.description,
    ],
    { cacheKey, cacheTtlMs: 60_000 }
  );

  const points: ChartSeriesPoint[] =
    data?.points.map((point) => ({
      periodo: point.periodo,
      sortKey: point.sort_key,
      dateStart: point.date_start,
      dateEnd: point.date_end,
      value: point.value,
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
