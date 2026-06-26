import { useCallback, useEffect, useState } from "react";

import { formatQualityApiError } from "../utils/formatQualityApiError";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";
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
  ppmInternalBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmExternalBranches: PerBranchMetricSlices<PpmSummary> | null;
  kaizenIdeasBranches: PerBranchMetricSlices | null;
  kaizenSavingsBranches: PerBranchMetricSlices<KaizenSummary> | null;
  audit5sBranches: PerBranchMetricSlices<Audit5sSummary> | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
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
  const [ppmInternalBranches, setPpmInternalBranches] =
    useState<PerBranchMetricSlices<PpmSummary> | null>(null);
  const [ppmExternalBranches, setPpmExternalBranches] =
    useState<PerBranchMetricSlices<PpmSummary> | null>(null);
  const [kaizenIdeasBranches, setKaizenIdeasBranches] =
    useState<PerBranchMetricSlices | null>(null);
  const [kaizenSavingsBranches, setKaizenSavingsBranches] =
    useState<PerBranchMetricSlices<KaizenSummary> | null>(null);
  const [audit5sBranches, setAudit5sBranches] =
    useState<PerBranchMetricSlices<Audit5sSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

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

        const needsBranchIdd = !stableFilters.branch;

        const results = await runParallelWithProgress(
          [
            (signal) => getPpmInternalSummary(ppmParams, signal),
            (signal) => getPpmExternalSummary(ppmParams, signal),
            (signal) => getKaizenSummary(kaizenParams, signal),
            (signal) => getAudit5sSummary(auditParams, signal),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmInternalSummary(
                          { ...ppmParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ppm,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmExternalSummary(
                          { ...ppmParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ppm,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getKaizenSummary(
                          { ...kaizenParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.total_kaizens,
                      signal,
                      (data) => data.ideas_goal ?? data,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getKaizenSummary(
                          { ...kaizenParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.total_savings,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getAudit5sSummary(
                          { ...auditParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.average_score,
                      signal,
                    ),
                ]
              : []),
          ] as ReadonlyArray<(signal: AbortSignal) => Promise<unknown>>,
          controller.signal,
          setRequestProgress
        );

        const nextErrors: SectionErrors = {};
        let successCount = 0;

        if (results[0].status === "fulfilled") {
          setPpmInternal(results[0].value as PpmSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.ppmInternal =
            formatQualityApiError(results[0].reason) ||
            "Erro ao carregar PPM interno";
        }

        if (results[1].status === "fulfilled") {
          setPpmExternal(results[1].value as PpmSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.ppmExternal =
            formatQualityApiError(results[1].reason) ||
            "Erro ao carregar PPM externo";
        }

        if (results[2].status === "fulfilled") {
          setKaizen(results[2].value as KaizenSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.kaizen =
            formatQualityApiError(results[2].reason) ||
            "Erro ao carregar kaizens";
        }

        if (results[3].status === "fulfilled") {
          setAudit5s(results[3].value as Audit5sSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.audit5s =
            formatQualityApiError(results[3].reason) ||
            "Erro ao carregar auditorias 5S";
        }

        if (!controller.signal.aborted && needsBranchIdd) {
          const branchSetters = [
            setPpmInternalBranches,
            setPpmExternalBranches,
            setKaizenIdeasBranches,
            setKaizenSavingsBranches,
            setAudit5sBranches,
          ];
          results.slice(4).forEach((result, index) => {
            if (result.status === "fulfilled") {
              branchSetters[index]?.(result.value as never);
            }
          });
        }

        if (!controller.signal.aborted && !needsBranchIdd) {
          setPpmInternalBranches(null);
          setPpmExternalBranches(null);
          setKaizenIdeasBranches(null);
          setKaizenSavingsBranches(null);
          setAudit5sBranches(null);
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
    ppmInternalBranches,
    ppmExternalBranches,
    kaizenIdeasBranches,
    kaizenSavingsBranches,
    audit5sBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  };
}
