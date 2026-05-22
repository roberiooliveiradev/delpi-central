import { useCallback, useEffect, useMemo, useState } from "react";
import { getLmpsDashboard } from "../api/engineeringApi";
import type { LmpDashboardItem, LmpsDashboardParams, LmpsDashboardResponse } from "../types/lmp";
import { formatEngineeringApiError } from "../utils/formatEngineeringApiError";
import { inputDateToLmpApi } from "../utils/lmpDates";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

export const LMP_DASHBOARD_PAGE_SIZE = 50;

type UseLmpsDashboardParams = LmpsDashboardParams;

export function useLmpsDashboard(params: UseLmpsDashboardParams) {
  const [data, setData] = useState<LmpsDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);
  const [page, setPage] = useState(1);
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
    }),
    [
      params.date_start,
      params.date_end,
      params.branch,
      params.listing_type,
      params.status,
    ]
  );

  useEffect(() => {
    setPage(1);
  }, [
    stableParams.branch,
    stableParams.date_end,
    stableParams.date_start,
    stableParams.listing_type,
    stableParams.status,
  ]);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = data !== null;

      try {
        setError(null);
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        const baseParams = {
          ...stableParams,
          page,
          page_size: LMP_DASHBOARD_PAGE_SIZE,
        };

        const results = await runParallelWithProgress(
          [
            (signal) =>
              getLmpsDashboard(
                { ...baseParams, scope: "aggregates" },
                signal
              ),
            (signal) =>
              getLmpsDashboard({ ...baseParams, scope: "items" }, signal),
          ],
          controller.signal,
          setRequestProgress
        );

        if (controller.signal.aborted) {
          return;
        }

        const aggregates =
          results[0].status === "fulfilled"
            ? (results[0].value as LmpsDashboardResponse)
            : null;
        const itemsPayload =
          results[1].status === "fulfilled"
            ? (results[1].value as LmpsDashboardResponse)
            : null;

        if (!aggregates && !itemsPayload) {
          const reason =
            results[0].status === "rejected"
              ? results[0].reason
              : results[1].status === "rejected"
                ? results[1].reason
                : new Error("Erro ao carregar LMPs");
          throw reason;
        }

        setData({
          items: itemsPayload?.items ?? [],
          total: aggregates?.total ?? itemsPayload?.total ?? 0,
          page: itemsPayload?.page ?? page,
          page_size: itemsPayload?.page_size ?? LMP_DASHBOARD_PAGE_SIZE,
          summary: aggregates?.summary ?? null,
          charts: aggregates?.charts ?? null,
        });

        if (aggregates && !itemsPayload) {
          setError("Indicadores carregados; falha ao listar registros.");
        } else if (!aggregates && itemsPayload) {
          setError("Registros carregados; falha nos indicadores agregados.");
        }
      } catch (reason) {
        if (!controller.signal.aborted) {
          setError(formatEngineeringApiError(reason));
        }
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
  }, [
    stableParams.branch,
    stableParams.date_end,
    stableParams.date_start,
    stableParams.listing_type,
    stableParams.status,
    page,
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
    total: data?.total ?? 0,
    page: data?.page ?? page,
    pageSize: data?.page_size ?? LMP_DASHBOARD_PAGE_SIZE,
    setPage,
    loading,
    refreshing,
    requestProgress,
    error,
    reload,
  };
}
