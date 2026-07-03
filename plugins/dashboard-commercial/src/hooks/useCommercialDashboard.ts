import { useCallback, useEffect, useState } from "react";
import {
  getBranchNewBusinessRolTarget,
  getBranchRolTarget,
  getBranchWegRolTarget,
  getClosingRate,
  getHeadOfficeNewBusinessRolTarget,
  getHeadOfficeRolTarget,
  getHeadOfficeWegRolTarget,
  getNewBusinessRolPct,
  getSalesOrderOtd,
} from "../api/commercialApi";
import { formatCommercialApiError } from "../utils/formatCommercialApiError";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";
import type {
  ClosingRateData,
  CommercialFilterParams,
  NewBusinessRolPctData,
  RolTargetData,
  SalesOrderOtdData,
} from "../types/commercial";

type SectionErrors = {
  headOfficeRol?: string;
  branchRol?: string;
  headOfficeWegRol?: string;
  branchWegRol?: string;
  headOfficeNewBusinessRol?: string;
  branchNewBusinessRol?: string;
  closingRate?: string;
  salesOrderOtd?: string;
  newBusinessRol?: string;
};

type UseCommercialDashboardResult = {
  headOfficeRol: RolTargetData | null;
  branchRol: RolTargetData | null;
  headOfficeWegRol: RolTargetData | null;
  branchWegRol: RolTargetData | null;
  headOfficeNewBusinessRol: RolTargetData | null;
  branchNewBusinessRol: RolTargetData | null;
  closingRate: ClosingRateData | null;
  salesOrderOtd: SalesOrderOtdData | null;
  newBusinessRol: NewBusinessRolPctData | null;
  closingRateBranches: PerBranchMetricSlices<ClosingRateData> | null;
  salesOrderOtdBranches: PerBranchMetricSlices<SalesOrderOtdData> | null;
  newBusinessRolBranches: PerBranchMetricSlices<NewBusinessRolPctData> | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  sectionErrors: SectionErrors;
  reload: () => void;
};

export function useCommercialDashboard(
  filters: CommercialFilterParams
): UseCommercialDashboardResult {
  const [headOfficeRol, setHeadOfficeRol] = useState<RolTargetData | null>(null);
  const [branchRol, setBranchRol] = useState<RolTargetData | null>(null);
  const [headOfficeWegRol, setHeadOfficeWegRol] = useState<RolTargetData | null>(
    null
  );
  const [branchWegRol, setBranchWegRol] = useState<RolTargetData | null>(null);
  const [headOfficeNewBusinessRol, setHeadOfficeNewBusinessRol] =
    useState<RolTargetData | null>(null);
  const [branchNewBusinessRol, setBranchNewBusinessRol] =
    useState<RolTargetData | null>(null);
  const [closingRate, setClosingRate] = useState<ClosingRateData | null>(null);
  const [salesOrderOtd, setSalesOrderOtd] = useState<SalesOrderOtdData | null>(null);
  const [newBusinessRol, setNewBusinessRol] = useState<NewBusinessRolPctData | null>(
    null
  );
  const [closingRateBranches, setClosingRateBranches] =
    useState<PerBranchMetricSlices<ClosingRateData> | null>(null);
  const [salesOrderOtdBranches, setSalesOrderOtdBranches] =
    useState<PerBranchMetricSlices<SalesOrderOtdData> | null>(null);
  const [newBusinessRolBranches, setNewBusinessRolBranches] =
    useState<PerBranchMetricSlices<NewBusinessRolPctData> | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);
  const [requestProgress, setRequestProgress] = useState<RequestProgress>(
    EMPTY_REQUEST_PROGRESS
  );

  const indicatorParams = filters;

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousData =
        headOfficeRol !== null ||
        branchRol !== null ||
        headOfficeWegRol !== null ||
        branchWegRol !== null ||
        headOfficeNewBusinessRol !== null ||
        branchNewBusinessRol !== null ||
        closingRate !== null ||
        salesOrderOtd !== null ||
        newBusinessRol !== null;

      try {
        setError(null);
        setSectionErrors({});

        if (hasPreviousData) setRefreshing(true);
        else setLoading(true);

        const needsBranchIdd = !indicatorParams.branch;

        const segmentRolParams = {
          start_date: indicatorParams.start_date,
          end_date: indicatorParams.end_date,
          branch: indicatorParams.branch,
        };

        const results = await runParallelWithProgress(
          [
            (signal) => getHeadOfficeRolTarget(indicatorParams, signal),
            (signal) => getBranchRolTarget(indicatorParams, signal),
            (signal) => getHeadOfficeWegRolTarget(segmentRolParams, signal),
            (signal) => getBranchWegRolTarget(segmentRolParams, signal),
            (signal) =>
              getHeadOfficeNewBusinessRolTarget(segmentRolParams, signal),
            (signal) => getBranchNewBusinessRolTarget(segmentRolParams, signal),
            (signal) => getClosingRate(indicatorParams, signal),
            (signal) => getSalesOrderOtd(indicatorParams, signal),
            (signal) => getNewBusinessRolPct(indicatorParams, signal),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getClosingRate(
                          { ...indicatorParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.sales_conversion_rate_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getSalesOrderOtd(
                          { ...indicatorParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.sales_order_otd_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getNewBusinessRolPct(
                          { ...indicatorParams, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.new_business_rol_pct,
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
          { key: "headOfficeRol", set: setHeadOfficeRol as (v: unknown) => void },
          { key: "branchRol", set: setBranchRol as (v: unknown) => void },
          {
            key: "headOfficeWegRol",
            set: setHeadOfficeWegRol as (v: unknown) => void,
          },
          { key: "branchWegRol", set: setBranchWegRol as (v: unknown) => void },
          {
            key: "headOfficeNewBusinessRol",
            set: setHeadOfficeNewBusinessRol as (v: unknown) => void,
          },
          {
            key: "branchNewBusinessRol",
            set: setBranchNewBusinessRol as (v: unknown) => void,
          },
          { key: "closingRate", set: setClosingRate as (v: unknown) => void },
          { key: "salesOrderOtd", set: setSalesOrderOtd as (v: unknown) => void },
          { key: "newBusinessRol", set: setNewBusinessRol as (v: unknown) => void },
        ];

        results.forEach((result, index) => {
          if (index < handlers.length) {
            const { key, set } = handlers[index];
            if (result.status === "fulfilled") {
              set(result.value);
              successCount += 1;
            } else if (!controller.signal.aborted) {
              nextErrors[key] =
                formatCommercialApiError(result.reason) ||
                "Erro ao carregar indicador";
            }
            return;
          }

          if (controller.signal.aborted || result.status !== "fulfilled") {
            return;
          }

          const branchIndex = index - handlers.length;
          if (branchIndex === 0) {
            setClosingRateBranches(
              result.value as PerBranchMetricSlices<ClosingRateData>,
            );
          } else if (branchIndex === 1) {
            setSalesOrderOtdBranches(
              result.value as PerBranchMetricSlices<SalesOrderOtdData>,
            );
          } else if (branchIndex === 2) {
            setNewBusinessRolBranches(
              result.value as PerBranchMetricSlices<NewBusinessRolPctData>,
            );
          }
        });

        if (!controller.signal.aborted) {
          if (!needsBranchIdd) {
            setClosingRateBranches(null);
            setSalesOrderOtdBranches(null);
            setNewBusinessRolBranches(null);
          }
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
    indicatorParams.branch,
    indicatorParams.customer_segment,
    indicatorParams.end_date,
    indicatorParams.start_date,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    headOfficeRol,
    branchRol,
    headOfficeWegRol,
    branchWegRol,
    headOfficeNewBusinessRol,
    branchNewBusinessRol,
    closingRate,
    salesOrderOtd,
    newBusinessRol,
    closingRateBranches,
    salesOrderOtdBranches,
    newBusinessRolBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  };
}
