import { useCallback } from "react";

import { getSalesOrderOtdSeries } from "../api/commercialApi";
import type { ChartGranularity } from "../types/chart";
import type { CommercialFilterParams } from "../types/commercial";
import { useCommercialResource } from "./useCommercialResource";

export type SalesOrderOtdSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  otdFilial01: number | null;
  otdFilial02: number | null;
};

type UseCommercialSalesOrderOtdSeriesParams = {
  filters: Pick<
    CommercialFilterParams,
    "start_date" | "end_date" | "branch" | "customer_segment"
  >;
  granularity: ChartGranularity;
};

export function useCommercialSalesOrderOtdSeries({
  filters,
  granularity,
}: UseCommercialSalesOrderOtdSeriesParams) {
  const cacheKey = [
    "sales-order-otd-series",
    granularity,
    filters.start_date ?? "",
    filters.end_date ?? "",
    filters.branch ?? "",
    filters.customer_segment ?? "",
  ].join(":");

  const { data, loading, error, reload } = useCommercialResource(
    (signal) =>
      getSalesOrderOtdSeries(
        {
          start_date: filters.start_date,
          end_date: filters.end_date,
          branch: filters.branch,
          customer_segment: filters.customer_segment,
          granularity,
        },
        signal
      ),
    [
      granularity,
      filters.start_date,
      filters.end_date,
      filters.branch,
      filters.customer_segment,
    ],
    { cacheKey, cacheTtlMs: 60_000 }
  );

  const points: SalesOrderOtdSeriesPoint[] =
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
