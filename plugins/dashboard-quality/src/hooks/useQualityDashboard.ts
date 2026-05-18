import { useCallback, useEffect, useMemo, useState } from "react";
import {
  getAudit5sSummary,
  getKaizenSummary,
  getPpmExternalSummary,
  getPpmInternalSummary,
} from "../api/qualityApi";
import { inputDateToApi } from "../utils/dates";
import type { Audit5sSummary } from "../types/audit5s";
import type { KaizenSummary } from "../types/kaizen";
import type { PpmSummary } from "../types/ppm";

export type QualityDashboardFilters = {
  branch?: string;
  date_start?: string;
  date_end?: string;
};

export type QualityDashboardData = {
  ppmInternal: PpmSummary;
  ppmExternal: PpmSummary;
  kaizen: KaizenSummary;
  audit5s: Audit5sSummary;
};

type UseQualityDashboardResult = {
  data: QualityDashboardData | null;
  ppmInternal: PpmSummary | null;
  ppmExternal: PpmSummary | null;
  kaizen: KaizenSummary | null;
  audit5s: Audit5sSummary | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  reload: () => void;
};

export function useQualityDashboard(
  filters: QualityDashboardFilters
): UseQualityDashboardResult {
  const [data, setData] = useState<QualityDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const stableFilters = useMemo(
    () => ({
      branch: filters.branch || undefined,
      date_start: inputDateToApi(filters.date_start),
      date_end: inputDateToApi(filters.date_end),
    }),
    [filters.branch, filters.date_start, filters.date_end]
  );

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousData = data !== null;

      try {
        setError(null);

        if (hasPreviousData) {
          setRefreshing(true);
        } else {
          setLoading(true);
        }

        const ppmParams = {
          branch: stableFilters.branch,
          date_start: stableFilters.date_start,
          date_end: stableFilters.date_end,
        };

        const kaizenParams = {
          branch: stableFilters.branch,
          date_start: stableFilters.date_start,
          date_end: stableFilters.date_end,
        };

        const auditParams = {
          branch: stableFilters.branch,
          start_date: stableFilters.date_start,
          end_date: stableFilters.date_end,
        };

        const [ppmInternal, ppmExternal, kaizen, audit5s] = await Promise.all([
          getPpmInternalSummary(ppmParams, controller.signal),
          getPpmExternalSummary(ppmParams, controller.signal),
          getKaizenSummary(kaizenParams, controller.signal),
          getAudit5sSummary(auditParams, controller.signal),
        ]);

        setData({ ppmInternal, ppmExternal, kaizen, audit5s });
      } catch (err) {
        if (controller.signal.aborted) return;

        setError(
          err instanceof Error
            ? err.message
            : "Erro ao carregar dashboard de qualidade"
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
  }, [stableFilters, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    data,
    ppmInternal: data?.ppmInternal ?? null,
    ppmExternal: data?.ppmExternal ?? null,
    kaizen: data?.kaizen ?? null,
    audit5s: data?.audit5s ?? null,
    loading,
    refreshing,
    error,
    reload,
  };
}
