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
import { PLUGS_PRODUCT_PREFIX } from "../utils/ppmProductScope";
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
  ppmInternalPlugs?: string;
  ppmExternalPlugs?: string;
  kaizen?: string;
  audit5s?: string;
};

type UseQualityDashboardResult = {
  ppmInternal: PpmSummary | null;
  ppmExternal: PpmSummary | null;
  ppmInternalPlugs: PpmSummary | null;
  ppmExternalPlugs: PpmSummary | null;
  kaizen: KaizenSummary | null;
  audit5s: Audit5sSummary | null;
  ppmInternalBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmExternalBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmInternalPlugsBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmExternalPlugsBranches: PerBranchMetricSlices<PpmSummary> | null;
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
  const [ppmInternalPlugs, setPpmInternalPlugs] = useState<PpmSummary | null>(null);
  const [ppmExternalPlugs, setPpmExternalPlugs] = useState<PpmSummary | null>(null);
  const [kaizen, setKaizen] = useState<KaizenSummary | null>(null);
  const [audit5s, setAudit5s] = useState<Audit5sSummary | null>(null);
  const [ppmInternalBranches, setPpmInternalBranches] =
    useState<PerBranchMetricSlices<PpmSummary> | null>(null);
  const [ppmExternalBranches, setPpmExternalBranches] =
    useState<PerBranchMetricSlices<PpmSummary> | null>(null);
  const [ppmInternalPlugsBranches, setPpmInternalPlugsBranches] =
    useState<PerBranchMetricSlices<PpmSummary> | null>(null);
  const [ppmExternalPlugsBranches, setPpmExternalPlugsBranches] =
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
        ppmInternalPlugs !== null ||
        ppmExternalPlugs !== null ||
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

        const basePpmParams = {
          branch: stableFilters.branch,
          date_start: stableFilters.date_start,
          date_end: stableFilters.date_end,
        };

        const plugsPpmParams = {
          ...basePpmParams,
          product_prefix: PLUGS_PRODUCT_PREFIX,
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
            (signal) => getPpmInternalSummary(basePpmParams, signal),
            (signal) => getPpmExternalSummary(basePpmParams, signal),
            (signal) => getPpmInternalSummary(plugsPpmParams, signal),
            (signal) => getPpmExternalSummary(plugsPpmParams, signal),
            (signal) => getKaizenSummary(kaizenParams, signal),
            (signal) => getAudit5sSummary(auditParams, signal),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmInternalSummary(
                          { ...basePpmParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ppm,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmExternalSummary(
                          { ...basePpmParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ppm,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmInternalSummary(
                          { ...plugsPpmParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ppm,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmExternalSummary(
                          { ...plugsPpmParams, branch },
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

        const ppmSetters = [
          { index: 0, set: setPpmInternal, key: "ppmInternal" as const },
          { index: 1, set: setPpmExternal, key: "ppmExternal" as const },
          { index: 2, set: setPpmInternalPlugs, key: "ppmInternalPlugs" as const },
          { index: 3, set: setPpmExternalPlugs, key: "ppmExternalPlugs" as const },
        ];

        for (const entry of ppmSetters) {
          const result = results[entry.index];
          if (result.status === "fulfilled") {
            entry.set(result.value as PpmSummary);
            successCount += 1;
          } else if (!controller.signal.aborted) {
            nextErrors[entry.key] =
              formatQualityApiError(result.reason) ||
              "Erro ao carregar PPM";
          }
        }

        if (results[4].status === "fulfilled") {
          setKaizen(results[4].value as KaizenSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.kaizen =
            formatQualityApiError(results[4].reason) ||
            "Erro ao carregar kaizens";
        }

        if (results[5].status === "fulfilled") {
          setAudit5s(results[5].value as Audit5sSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.audit5s =
            formatQualityApiError(results[5].reason) ||
            "Erro ao carregar auditorias 5S";
        }

        if (!controller.signal.aborted && needsBranchIdd) {
          const branchSetters = [
            setPpmInternalBranches,
            setPpmExternalBranches,
            setPpmInternalPlugsBranches,
            setPpmExternalPlugsBranches,
            setKaizenIdeasBranches,
            setKaizenSavingsBranches,
            setAudit5sBranches,
          ];
          results.slice(6).forEach((result, index) => {
            if (result.status === "fulfilled") {
              branchSetters[index]?.(result.value as never);
            }
          });
        }

        if (!controller.signal.aborted && !needsBranchIdd) {
          setPpmInternalBranches(null);
          setPpmExternalBranches(null);
          setPpmInternalPlugsBranches(null);
          setPpmExternalPlugsBranches(null);
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
    ppmInternalPlugs,
    ppmExternalPlugs,
    kaizen,
    audit5s,
    ppmInternalBranches,
    ppmExternalBranches,
    ppmInternalPlugsBranches,
    ppmExternalPlugsBranches,
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
