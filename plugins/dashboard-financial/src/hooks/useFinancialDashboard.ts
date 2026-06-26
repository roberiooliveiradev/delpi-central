import { useCallback, useEffect, useState } from "react";
import {
  getEbitdaPct,
  getFixedCostPct,
  getPmr,
  getRol,
} from "../api/financialApi";
import type {
  EbitdaPctData,
  FinancialFilterParams,
  FixedCostPctData,
  PmrData,
  RolData,
} from "../types/financial";
import { formatFinancialApiError } from "../utils/formatFinancialApiError";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

type SectionErrors = {
  rol?: string;
  ebitda?: string;
  fixedCost?: string;
  pmr?: string;
};

export function useFinancialDashboard(apiParams: FinancialFilterParams) {
  const [rol, setRol] = useState<RolData | null>(null);
  const [ebitda, setEbitda] = useState<EbitdaPctData | null>(null);
  const [fixedCost, setFixedCost] = useState<FixedCostPctData | null>(null);
  const [pmr, setPmr] = useState<PmrData | null>(null);
  const [ebitdaBranches, setEbitdaBranches] =
    useState<PerBranchMetricSlices<EbitdaPctData> | null>(null);
  const [fixedCostBranches, setFixedCostBranches] =
    useState<PerBranchMetricSlices<FixedCostPctData> | null>(null);
  const [pmrBranches, setPmrBranches] =
    useState<PerBranchMetricSlices<PmrData> | null>(null);
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
      const hasPreviousData =
        rol !== null || ebitda !== null || fixedCost !== null || pmr !== null;

      try {
        setError(null);
        setSectionErrors({});

        if (hasPreviousData) setRefreshing(true);
        else setLoading(true);

        const needsBranchIdd = !apiParams.branch;

        const results = await runParallelWithProgress(
          [
            (signal) => getRol(apiParams, signal),
            (signal) => getEbitdaPct(apiParams, signal),
            (signal) => getFixedCostPct(apiParams, signal),
            (signal) => getPmr(apiParams, signal),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getEbitdaPct(
                          { ...apiParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.ebitda_over_rol_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getFixedCostPct(
                          { ...apiParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.fixed_cost_over_rol_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getPmr({ ...apiParams, branch }, branchSignal ?? signal),
                      (data) => data.pmr_days,
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

        const handlers: Array<{
          key: keyof SectionErrors;
          set: (v: unknown) => void;
        }> = [
          { key: "rol", set: setRol as (v: unknown) => void },
          { key: "ebitda", set: setEbitda as (v: unknown) => void },
          { key: "fixedCost", set: setFixedCost as (v: unknown) => void },
          { key: "pmr", set: setPmr as (v: unknown) => void },
        ];

        results.forEach((result, index) => {
          if (index < handlers.length) {
            const { key, set } = handlers[index];
            if (result.status === "fulfilled") {
              set(result.value);
              successCount += 1;
            } else if (!controller.signal.aborted) {
              nextErrors[key] =
                formatFinancialApiError(result.reason) ||
                "Erro ao carregar indicador";
            }
            return;
          }

          if (controller.signal.aborted || result.status !== "fulfilled") {
            return;
          }

          const branchSetters = [
            setEbitdaBranches,
            setFixedCostBranches,
            setPmrBranches,
          ];
          branchSetters[index - handlers.length]?.(result.value as never);
        });

        if (!controller.signal.aborted && !needsBranchIdd) {
          setEbitdaBranches(null);
          setFixedCostBranches(null);
          setPmrBranches(null);
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
  }, [apiParams.branch, apiParams.end_date, apiParams.start_date, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    rol,
    ebitda,
    fixedCost,
    pmr,
    ebitdaBranches,
    fixedCostBranches,
    pmrBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  };
}
