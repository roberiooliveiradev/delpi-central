import { useCallback } from "react";

import { getProductionOtdSeries } from "../api/productionApi";
import type { ChartGranularity } from "../types/chart";
import type { ProductionFilterParams } from "../types/production";
import { useProductionResource } from "./useProductionResource";

export type OtdSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  otdFilial01: number | null;
  otdFilial02: number | null;
};

type UseProductionOtdSeriesParams = {
  filters: ProductionFilterParams;
  granularity: ChartGranularity;
};

type UseProductionOtdSeriesResult = {
  points: OtdSeriesPoint[];
  loading: boolean;
  truncated: boolean;
  error: string | null;
  reload: () => void;
};

export function useProductionOtdSeries({
  filters,
  granularity,
}: UseProductionOtdSeriesParams): UseProductionOtdSeriesResult {
  const cacheKey = [
    "otd-series",
    granularity,
    filters.start_date ?? "",
    filters.end_date ?? "",
    filters.branch ?? "",
  ].join(":");

  const { data, loading, error, reload } = useProductionResource(
    (signal) =>
      getProductionOtdSeries(
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

  const points: OtdSeriesPoint[] =
    data?.points.map((point) => ({
      periodo: point.periodo,
      sortKey: point.sort_key,
      dateStart: point.date_start,
      dateEnd: point.date_end,
      otdFilial01: point.otd_filial_01,
      otdFilial02: point.otd_filial_02,
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
