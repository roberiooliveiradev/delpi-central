import { useCallback, useEffect, useRef, useState } from "react";

import {
  fetchAppointmentsSeries,
  fetchAppointmentsSummary,
  fetchWorkCenters,
} from "../api/appointmentsApi";
import type {
  AppointmentsQueryFilters,
  AppointmentsSeriesData,
  AppointmentsSummaryData,
  WorkCenterItem,
} from "../types/appointments";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

export type DashboardLoadState = "idle" | "loading" | "success" | "error";

export type AppointmentsDashboardData = {
  summary: AppointmentsSummaryData | null;
  series: AppointmentsSeriesData | null;
  workCenters: WorkCenterItem[];
};

const emptyDashboard: AppointmentsDashboardData = {
  summary: null,
  series: null,
  workCenters: [],
};

function hasRequiredFilters(
  filters: AppointmentsQueryFilters | null,
): filters is AppointmentsQueryFilters {
  return Boolean(filters?.branch && filters.dateStart && filters.dateEnd);
}

export function useAppointmentsDashboard(appliedFilters: AppointmentsQueryFilters | null) {
  const [state, setState] = useState<DashboardLoadState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<AppointmentsDashboardData>(emptyDashboard);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS,
  );
  const [reloadKey, setReloadKey] = useState(0);
  const dataRef = useRef(data);
  dataRef.current = data;

  const reload = useCallback(() => {
    setReloadKey((current) => current + 1);
  }, []);

  useEffect(() => {
    if (!hasRequiredFilters(appliedFilters)) {
      setState("idle");
      setData(emptyDashboard);
      setError(null);
      setLoading(false);
      setRefreshing(false);
      setRequestProgress(EMPTY_REQUEST_PROGRESS);
      return;
    }

    const controller = new AbortController();
    const filters = appliedFilters;
    const hasPreviousData = dataRef.current.summary !== null;

    async function run() {
      try {
        setError(null);
        setRequestProgress(EMPTY_REQUEST_PROGRESS);

        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
          setState("loading");
        }

        const results = await runParallelWithProgress<unknown>(
          [
            (signal) => fetchAppointmentsSummary(filters, { signal }),
            (signal) => fetchAppointmentsSeries(filters, "day", { signal }),
            (signal) => fetchWorkCenters(filters.branch, { signal }),
          ],
          controller.signal,
          setRequestProgress,
        );

        const rejected = results.find((result) => result.status === "rejected");
        if (rejected && rejected.status === "rejected") {
          throw rejected.reason;
        }

        const values = results.map((result) =>
          result.status === "fulfilled" ? result.value : null,
        );

        setData({
          summary: values[0] as AppointmentsSummaryData,
          series: values[1] as AppointmentsSeriesData,
          workCenters: ((values[2] as { items: WorkCenterItem[] })?.items) ?? [],
        });
        setState("success");
      } catch (err) {
        if (controller.signal.aborted) return;
        const message =
          err instanceof Error ? err.message : "Falha ao carregar o painel.";
        setError(message);
        setState("error");
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setRefreshing(false);
        }
      }
    }

    void run();
    return () => controller.abort();
  }, [appliedFilters, reloadKey]);

  return {
    state,
    error,
    data,
    loading,
    refreshing,
    requestProgress,
    reload,
  };
}
