import { useCallback, useEffect, useState } from "react";
import { getPpmSummary, listPpm } from "../api/qualityApi";
import type {
  PpmItem,
  PpmSummary,
  PpmType,
  DateRangeParams,
  ListPpmParams,
} from "../types/ppm";
import type { Page } from "../types/pagination";

const DEFAULT_PAGE_SIZE = 20;

type UsePpmPageParams = {
  type: PpmType;
  filters: DateRangeParams;
  page: number;
  pageSize?: number;
};

type UsePpmPageResult = {
  summary: PpmSummary | null;
  page: Page<PpmItem> | null;
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
  pageSize = DEFAULT_PAGE_SIZE,
}: UsePpmPageParams): UsePpmPageResult {
  const [summary, setSummary] = useState<PpmSummary | null>(null);
  const [tablePage, setTablePage] = useState<Page<PpmItem> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const stableFilters = {
    branch: filters.branch,
    date_start: filters.date_start,
    date_end: filters.date_end,
  };

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
          page_size: pageSize,
        };

        const [summaryResult, tableResult] = await Promise.all([
          getPpmSummary(type, stableFilters, controller.signal),
          listPpm(type, listParams, controller.signal),
        ]);

        setSummary(summaryResult);
        setTablePage(tableResult);
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
  }, [type, page, pageSize, stableFilters.branch, stableFilters.date_start, stableFilters.date_end, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    summary,
    page: tablePage,
    loading,
    refreshing,
    error,
    reload,
    pageSize,
  };
}
