import { useCallback, useEffect, useMemo, useState } from "react";
import { getLmpsDashboard } from "../api/engineeringApi";
import type { LmpDashboardItem, LmpsDashboardParams, LmpsDashboardResponse } from "../types/lmp";
import { formatEngineeringApiError } from "../utils/formatEngineeringApiError";
import { inputDateToLmpApi } from "../utils/lmpDates";
import {
  beginSingleRequestProgress,
  EMPTY_REQUEST_PROGRESS,
  finishSingleRequestProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

type UseLmpsDashboardParams = LmpsDashboardParams;

export function useLmpsDashboard(params: UseLmpsDashboardParams) {
  const [data, setData] = useState<LmpsDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const stableParams = useMemo(
    () => ({
      date_start: inputDateToLmpApi(params.date_start),
      date_end: inputDateToLmpApi(params.date_end),
      branch: params.branch,
      listing_type: params.listing_type,
      status: params.status,
      page: params.page,
      page_size: params.page_size,
    }),
    [
      params.date_start,
      params.date_end,
      params.branch,
      params.listing_type,
      params.status,
      params.page,
      params.page_size,
    ]
  );

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = data !== null;

      try {
        setError(null);
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        beginSingleRequestProgress(setRequestProgress);
        const result = await getLmpsDashboard(stableParams, controller.signal);

        if (!controller.signal.aborted) {
          setData(result);
        }
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatEngineeringApiError(reason));
        }
      } finally {
        if (!controller.signal.aborted) {
          finishSingleRequestProgress(setRequestProgress, controller.signal.aborted);
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();

    return () => controller.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    stableParams.branch,
    stableParams.date_end,
    stableParams.date_start,
    stableParams.listing_type,
    stableParams.status,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    data,
    items: (data?.items ?? []) as LmpDashboardItem[],
    summary: data?.summary ?? null,
    charts: data?.charts ?? null,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
