import { useCallback } from "react";

import { getProductionOeeSeries } from "../api/productionApi";
import type { ChartGranularity } from "../types/chart";
import type { ProductionFilterParams } from "../types/production";
import { useProductionResource } from "./useProductionResource";

export type OeeSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  oeeFilial01: number | null;
  oeeFilial02: number | null;
};

type UseProductionOeeSeriesParams = {
  filters: ProductionFilterParams;
  granularity: ChartGranularity;
};

type UseProductionOeeSeriesResult = {
  points: OeeSeriesPoint[];
  loading: boolean;
  truncated: boolean;
  error: string | null;
  reload: () => void;
};

export function useProductionOeeSeries({
  filters,
  granularity,
}: UseProductionOeeSeriesParams): UseProductionOeeSeriesResult {
  const cacheKey = [
    "oee-series",
    granularity,
    filters.start_date ?? "",
    filters.end_date ?? "",
    filters.branch ?? "",
  ].join(":");

  const { data, loading, error, reload } = useProductionResource(
    (signal) =>
      getProductionOeeSeries(
        {
          start_date: filters.start_date,
          end_date: filters.end_date,
          branch: filters.branch,
          granularity,
        },
        signal
      ),
    [granularity, filters.start_date, filters.end_date, filters.branch],
    { cacheKey, cacheTtlMs: 60_000 }
  );

  const points: OeeSeriesPoint[] =
    data?.points.map((point) => ({
      periodo: point.periodo,
      sortKey: point.sort_key,
      dateStart: point.date_start,
      dateEnd: point.date_end,
      oeeFilial01: point.oee_filial_01,
      oeeFilial02: point.oee_filial_02,
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
