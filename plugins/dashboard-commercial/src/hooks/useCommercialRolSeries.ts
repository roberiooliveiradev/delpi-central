import { useCallback } from "react";

import { getCommercialRolSeries } from "../api/commercialApi";
import type { ChartGranularity } from "../types/chart";
import type { CommercialFilterParams } from "../types/commercial";
import { useCommercialResource } from "./useCommercialResource";

export type RolSeriesPoint = {
  periodo: string;
  sortKey: string;
  dateStart: string;
  dateEnd: string;
  rolMatrix: number;
  rolBranch: number;
};

type UseCommercialRolSeriesParams = {
  filters: Pick<
    CommercialFilterParams,
    "start_date" | "end_date" | "customer_segment"
  >;
  granularity: ChartGranularity;
};

type UseCommercialRolSeriesResult = {
  points: RolSeriesPoint[];
  loading: boolean;
  truncated: boolean;
  error: string | null;
  reload: () => void;
};

export function useCommercialRolSeries({
  filters,
  granularity,
}: UseCommercialRolSeriesParams): UseCommercialRolSeriesResult {
  const cacheKey = [
    "rol-series",
    granularity,
    filters.start_date ?? "",
    filters.end_date ?? "",
    filters.customer_segment ?? "",
  ].join(":");

  const { data, loading, error, reload } = useCommercialResource(
    (signal) =>
      getCommercialRolSeries(
        {
          start_date: filters.start_date,
          end_date: filters.end_date,
          customer_segment: filters.customer_segment,
          granularity,
        },
        signal
      ),
    [granularity, filters.start_date, filters.end_date, filters.customer_segment],
    { cacheKey, cacheTtlMs: 60_000 }
  );

  const points: RolSeriesPoint[] =
    data?.points.map((point) => ({
      periodo: point.periodo,
      sortKey: point.sort_key,
      dateStart: point.start_date,
      dateEnd: point.end_date,
      rolMatrix: point.rol_matrix,
      rolBranch: point.rol_branch,
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
