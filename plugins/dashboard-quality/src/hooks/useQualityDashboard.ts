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
import { PLUGS_PRODUCT_PREFIX, COMPONENTS_PRODUCT_PREFIX } from "../utils/ppmProductScope";
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
  start_date?: string;
  end_date?: string;
};

type SectionErrors = {
  ppmInternal?: string;
  ppmExternal?: string;
  ppmInternalPlugs?: string;
  ppmExternalPlugs?: string;
  ppmInternalComponents?: string;
  ppmExternalComponents?: string;
  kaizen?: string;
  audit5s?: string;
};

type UseQualityDashboardResult = {
  ppmInternal: PpmSummary | null;
  ppmExternal: PpmSummary | null;
  ppmInternalPlugs: PpmSummary | null;
  ppmExternalPlugs: PpmSummary | null;
  ppmInternalComponents: PpmSummary | null;
  ppmExternalComponents: PpmSummary | null;
  kaizen: KaizenSummary | null;
  audit5s: Audit5sSummary | null;
  ppmInternalBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmExternalBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmInternalPlugsBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmExternalPlugsBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmInternalComponentsBranches: PerBranchMetricSlices<PpmSummary> | null;
  ppmExternalComponentsBranches: PerBranchMetricSlices<PpmSummary> | null;
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
  const [ppmInternalComponents, setPpmInternalComponents] = useState<PpmSummary | null>(null);
  const [ppmExternalComponents, setPpmExternalComponents] = useState<PpmSummary | null>(null);
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
  const [ppmInternalComponentsBranches, setPpmInternalComponentsBranches] =
    useState<PerBranchMetricSlices<PpmSummary> | null>(null);
  const [ppmExternalComponentsBranches, setPpmExternalComponentsBranches] =
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
    start_date: inputDateToApi(filters.start_date),
    end_date: inputDateToApi(filters.end_date),
  };

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousData =
        ppmInternal !== null ||
        ppmExternal !== null ||
        ppmInternalPlugs !== null ||
        ppmExternalPlugs !== null ||
        ppmInternalComponents !== null ||
        ppmExternalComponents !== null ||
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
          start_date: stableFilters.start_date,
          end_date: stableFilters.end_date,
        };

        const plugsPpmParams = {
          ...basePpmParams,
          product_prefix: PLUGS_PRODUCT_PREFIX,
        };

        const componentsPpmParams = {
          ...basePpmParams,
          product_prefix: COMPONENTS_PRODUCT_PREFIX,
        };

        const kaizenParams = {
          branch: stableFilters.branch,
          start_date: stableFilters.start_date,
          end_date: stableFilters.end_date,
        };

        const auditParams = {
          branch: stableFilters.branch,
          start_date: stableFilters.start_date,
          end_date: stableFilters.end_date,
        };

        const needsBranchIdd = !stableFilters.branch;

        const results = await runParallelWithProgress(
          [
            (signal) => getPpmInternalSummary(basePpmParams, signal),
            (signal) => getPpmExternalSummary(basePpmParams, signal),
            (signal) => getPpmInternalSummary(plugsPpmParams, signal),
            (signal) => getPpmExternalSummary(plugsPpmParams, signal),
            (signal) => getPpmInternalSummary(componentsPpmParams, signal),
            (signal) => getPpmExternalSummary(componentsPpmParams, signal),
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
                        getPpmInternalSummary(
                          { ...componentsPpmParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ppm,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPpmExternalSummary(
                          { ...componentsPpmParams, branch },
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
          { index: 4, set: setPpmInternalComponents, key: "ppmInternalComponents" as const },
          { index: 5, set: setPpmExternalComponents, key: "ppmExternalComponents" as const },
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

        if (results[6].status === "fulfilled") {
          setKaizen(results[6].value as KaizenSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.kaizen =
            formatQualityApiError(results[6].reason) ||
            "Erro ao carregar kaizens";
        }

        if (results[7].status === "fulfilled") {
          setAudit5s(results[7].value as Audit5sSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.audit5s =
            formatQualityApiError(results[7].reason) ||
            "Erro ao carregar auditorias 5S";
        }

        if (!controller.signal.aborted && needsBranchIdd) {
          const branchSetters = [
            setPpmInternalBranches,
            setPpmExternalBranches,
            setPpmInternalPlugsBranches,
            setPpmExternalPlugsBranches,
            setPpmInternalComponentsBranches,
            setPpmExternalComponentsBranches,
            setKaizenIdeasBranches,
            setKaizenSavingsBranches,
            setAudit5sBranches,
          ];
          results.slice(8).forEach((result, index) => {
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
          setPpmInternalComponentsBranches(null);
          setPpmExternalComponentsBranches(null);
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
  }, [stableFilters.branch, stableFilters.start_date, stableFilters.end_date, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    ppmInternal,
    ppmExternal,
    ppmInternalPlugs,
    ppmExternalPlugs,
    ppmInternalComponents,
    ppmExternalComponents,
    kaizen,
    audit5s,
    ppmInternalBranches,
    ppmExternalBranches,
    ppmInternalPlugsBranches,
    ppmExternalPlugsBranches,
    ppmInternalComponentsBranches,
    ppmExternalComponentsBranches,
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
