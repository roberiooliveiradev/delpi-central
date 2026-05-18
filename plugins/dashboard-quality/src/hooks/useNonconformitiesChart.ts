import { useCallback, useEffect, useMemo, useState } from "react";
import { listNonconformities } from "../api/qualityApi";
import type { ChartGranularity } from "../types/chart";
import type { ListNonconformitiesParams, Nonconformity } from "../types/nonconformity";
import {
  aggregateQuantityByPeriod,
  type TimeSeriesPoint,
} from "../utils/timeSeriesAggregation";

const CHART_SAMPLE_SIZE = 500;

type UseNonconformitiesChartParams = {
  filters: Omit<ListNonconformitiesParams, "page" | "page_size">;
  dateStart?: string;
  dateEnd?: string;
  granularity: ChartGranularity;
};

type UseNonconformitiesChartResult = {
  points: TimeSeriesPoint[];
  sampleSize: number;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useNonconformitiesChart({
  filters,
  dateStart,
  dateEnd,
  granularity,
}: UseNonconformitiesChartParams): UseNonconformitiesChartResult {
  const [items, setItems] = useState<Nonconformity[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const stableFilters = useMemo(
    () => ({
      type: filters.type,
      branch: filters.branch,
      date_start: filters.date_start,
      date_end: filters.date_end,
      status: filters.status,
      item_code: filters.item_code,
      description: filters.description,
    }),
    [
      filters.type,
      filters.branch,
      filters.date_start,
      filters.date_end,
      filters.status,
      filters.item_code,
      filters.description,
    ]
  );

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      try {
        setLoading(true);
        setError(null);

        const result = await listNonconformities(
          {
            ...stableFilters,
            page: 1,
            page_size: CHART_SAMPLE_SIZE,
          },
          controller.signal
        );

        setItems(result.items);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar dados do gráfico"
        );
        setItems([]);
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    void run();

    return () => controller.abort();
  }, [stableFilters, reloadKey]);

  const points = useMemo(
    () =>
      aggregateQuantityByPeriod({
        items,
        getDate: (item) => item.registered_date,
        getQuantity: (item) => item.returned_quantity,
        dateStart,
        dateEnd,
        granularity,
      }),
    [items, dateStart, dateEnd, granularity]
  );

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    points,
    sampleSize: items.length,
    loading,
    error,
    reload,
  };
}
