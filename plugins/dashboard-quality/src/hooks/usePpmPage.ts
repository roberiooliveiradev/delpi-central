import { useCallback, useEffect, useMemo, useState } from "react";
import { getPpmSummary, listPpm } from "../api/qualityApi";
import type {
  PpmItem,
  PpmSummary,
  PpmType,
  DateRangeParams,
  ListPpmParams,
} from "../types/ppm";
import type { Page } from "../types/pagination";
import { aggregatePpmByMonth, type PpmChartPoint } from "../utils/ppmAggregation";

const TABLE_PAGE_SIZE = 20;
const CHART_SAMPLE_SIZE = 300;

type UsePpmPageParams = {
  type: PpmType;
  filters: DateRangeParams;
  page: number;
};

type UsePpmPageResult = {
  summary: PpmSummary | null;
  page: Page<PpmItem> | null;
  chartData: PpmChartPoint[];
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: () => void;
  pageSize: number;
};

export function usePpmPage({
  type,
  filters,
  page,
}: UsePpmPageParams): UsePpmPageResult {
  const [summary, setSummary] = useState<PpmSummary | null>(null);
  const [tablePage, setTablePage] = useState<Page<PpmItem> | null>(null);
  const [chartItems, setChartItems] = useState<PpmItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const stableFilters = useMemo(
    () => ({
      branch: filters.branch,
      date_start: filters.date_start,
      date_end: filters.date_end,
    }),
    [filters.branch, filters.date_start, filters.date_end]
  );

  const chartData = useMemo(
    () => aggregatePpmByMonth(chartItems),
    [chartItems]
  );

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasData = summary !== null || tablePage !== null;

      try {
        setError(null);

        if (hasData) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        const listParams: ListPpmParams = {
          ...stableFilters,
          page,
          page_size: TABLE_PAGE_SIZE,
        };

        const chartParams: ListPpmParams = {
          ...stableFilters,
          page: 1,
          page_size: CHART_SAMPLE_SIZE,
        };

        const [summaryResult, tableResult, chartResult] = await Promise.all([
          getPpmSummary(type, stableFilters, controller.signal),
          listPpm(type, listParams, controller.signal),
          listPpm(type, chartParams, controller.signal),
        ]);

        setSummary(summaryResult);
        setTablePage(tableResult);
        setChartItems(chartResult.items);
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error ? err.message : "Erro ao carregar dados de PPM"
        );
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [type, page, stableFilters, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    summary,
    page: tablePage,
    chartData,
    loading,
    refreshing,
    error,
    reload,
    pageSize: TABLE_PAGE_SIZE,
  };
}
