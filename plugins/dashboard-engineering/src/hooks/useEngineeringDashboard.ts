import { useCallback, useEffect, useState } from "react";
import { getLmpsDashboardSummary, getTransformaSummary } from "../api/engineeringApi";
import type { EngineeringFilterParams, TransformaSummary } from "../types/engineering";
import type { LmpsDashboardSummary } from "../types/lmp";
import { formatEngineeringApiError } from "../utils/formatEngineeringApiError";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";
import { inputDateToLmpApi } from "../utils/lmpDates";

type SectionErrors = {
  lmp?: string;
  transforma?: string;
};

export function useEngineeringDashboard(apiParams: EngineeringFilterParams) {
  const [transforma, setTransforma] = useState<TransformaSummary | null>(null);
  const [lmpSummary, setLmpSummary] = useState<LmpsDashboardSummary | null>(null);
  const [lmpBranches, setLmpBranches] =
    useState<PerBranchMetricSlices<LmpsDashboardSummary> | null>(null);
  const [transformaSavingsBranches, setTransformaSavingsBranches] =
    useState<PerBranchMetricSlices<TransformaSummary> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPrevious = transforma !== null || lmpSummary !== null;

      try {
        setError(null);
        setSectionErrors({});
        if (hasPrevious) setRefreshing(true);
        else setLoading(true);

        const lmpParams = {
          start_date: inputDateToLmpApi(apiParams.start_date),
          end_date: inputDateToLmpApi(apiParams.end_date),
          branch: apiParams.branch ?? apiParams.filial_id,
          status: "Todos",
        };

        const resolvedBranch = apiParams.branch ?? apiParams.filial_id;
        const needsBranchIdd = !resolvedBranch;

        const results = await runParallelWithProgress(
          [
            (signal) => getTransformaSummary(apiParams, signal),
            (signal) => getLmpsDashboardSummary(lmpParams, signal),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getLmpsDashboardSummary(
                          { ...lmpParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.percent_dentro_prazo,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getTransformaSummary(
                          { ...apiParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.total_gross_savings_in_period,
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
          setTransforma(results[0].value as TransformaSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.transforma =
            formatEngineeringApiError(results[0].reason) ||
            "Erro ao carregar TRANSFORMA+";
        }

        if (results[1].status === "fulfilled") {
          setLmpSummary(results[1].value as LmpsDashboardSummary);
          successCount += 1;
        } else if (!controller.signal.aborted) {
          nextErrors.lmp =
            formatEngineeringApiError(results[1].reason) || "Erro ao carregar LMPs";
        }

        if (!controller.signal.aborted && needsBranchIdd) {
          if (results[2]?.status === "fulfilled") {
            setLmpBranches(results[2].value as PerBranchMetricSlices<LmpsDashboardSummary>);
          }
          if (results[3]?.status === "fulfilled") {
            setTransformaSavingsBranches(
              results[3].value as PerBranchMetricSlices<TransformaSummary>,
            );
          }
        }

        if (!controller.signal.aborted && !needsBranchIdd) {
          setLmpBranches(null);
          setTransformaSavingsBranches(null);
        }

        if (!controller.signal.aborted) {
          setSectionErrors(nextErrors);
          setError(
            successCount === 0
              ? "Não foi possível carregar os indicadores do período."
              : null
          );
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
    apiParams.branch,
    apiParams.end_date,
    apiParams.filial_id,
    apiParams.start_date,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    transforma,
    lmpSummary,
    lmpBranches,
    transformaSavingsBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  };
}
