import { useCallback, useEffect, useState } from "react";

import { formatQualityApiError } from "../utils/formatQualityApiError";
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

type SectionErrors = {
  ppmInternal?: string;
  ppmExternal?: string;
  kaizen?: string;
  audit5s?: string;
};

type UseQualityDashboardResult = {
  ppmInternal: PpmSummary | null;
  ppmExternal: PpmSummary | null;
  kaizen: KaizenSummary | null;
  audit5s: Audit5sSummary | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  sectionErrors: SectionErrors;
  reload: () => void;
};

export function useQualityDashboard(
  filters: QualityDashboardFilters
): UseQualityDashboardResult {
  const [ppmInternal, setPpmInternal] = useState<PpmSummary | null>(null);
  const [ppmExternal, setPpmExternal] = useState<PpmSummary | null>(null);
  const [kaizen, setKaizen] = useState<KaizenSummary | null>(null);
  const [audit5s, setAudit5s] = useState<Audit5sSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);

  const stableFilters = {
    branch: filters.branch || undefined,
    date_start: inputDateToApi(filters.date_start),
    date_end: inputDateToApi(filters.date_end),
  };

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousData =
        ppmInternal !== null ||
        ppmExternal !== null ||
        kaizen !== null ||
        audit5s !== null;

      try {
        setError(null);
        setSectionErrors({});

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

        const results = await Promise.allSettled([
          getPpmInternalSummary(ppmParams, controller.signal),
          getPpmExternalSummary(ppmParams, controller.signal),
          getKaizenSummary(kaizenParams, controller.signal),
          getAudit5sSummary(auditParams, controller.signal),
        ]);

        const nextErrors: SectionErrors = {};
        let successCount = 0;

        if (results[0].status === "fulfilled") {
          setPpmInternal(results[0].value);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.ppmInternal =
            formatQualityApiError(results[0].reason) ||
            "Erro ao carregar PPM interno";
        }

        if (results[1].status === "fulfilled") {
          setPpmExternal(results[1].value);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.ppmExternal =
            formatQualityApiError(results[1].reason) ||
            "Erro ao carregar PPM externo";
        }

        if (results[2].status === "fulfilled") {
          setKaizen(results[2].value);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.kaizen =
            formatQualityApiError(results[2].reason) ||
            "Erro ao carregar kaizens";
        }

        if (results[3].status === "fulfilled") {
          setAudit5s(results[3].value);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.audit5s =
            formatQualityApiError(results[3].reason) ||
            "Erro ao carregar auditorias 5S";
        }

        if (!controller.signal.aborted) {
          setSectionErrors(nextErrors);

          if (successCount === 0) {
            setError("Não foi possível carregar os indicadores do período.");
          } else {
            setError(null);
          }
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
  }, [stableFilters.branch, stableFilters.date_start, stableFilters.date_end, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    ppmInternal,
    ppmExternal,
    kaizen,
    audit5s,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  };
}
