import { useCallback, useEffect, useState } from "react";
import {
  getDepreciationPct,
  getDirectLaborCostPct,
  getOnTimeDeliveryPct,
  getOverallEquipmentEffectivenessPct,
  getProductionCostPct,
} from "../api/productionApi";
import type {
  DepreciationPctData,
  DirectLaborCostPctData,
  OeePctData,
  OtdPctData,
  ProductionCostPctData,
  ProductionFilterParams,
} from "../types/production";
import { formatProductionApiError } from "../utils/formatProductionApiError";
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
  directLabor?: string;
  productionCost?: string;
  depreciation?: string;
  oee?: string;
  otd?: string;
};

type UseProductionDashboardResult = {
  directLabor: DirectLaborCostPctData | null;
  productionCost: ProductionCostPctData | null;
  depreciation: DepreciationPctData | null;
  oee: OeePctData | null;
  otd: OtdPctData | null;
  directLaborBranches: PerBranchMetricSlices<DirectLaborCostPctData> | null;
  productionCostBranches: PerBranchMetricSlices<ProductionCostPctData> | null;
  depreciationBranches: PerBranchMetricSlices<DepreciationPctData> | null;
  oeeBranches: PerBranchMetricSlices<OeePctData> | null;
  otdBranches: PerBranchMetricSlices<OtdPctData> | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  sectionErrors: SectionErrors;
  reload: () => void;
};

export function useProductionDashboard(
  filters: ProductionFilterParams
): UseProductionDashboardResult {
  const [directLabor, setDirectLabor] = useState<DirectLaborCostPctData | null>(
    null
  );
  const [productionCost, setProductionCost] =
    useState<ProductionCostPctData | null>(null);
  const [depreciation, setDepreciation] = useState<DepreciationPctData | null>(
    null
  );
  const [oee, setOee] = useState<OeePctData | null>(null);
  const [otd, setOtd] = useState<OtdPctData | null>(null);
  const [directLaborBranches, setDirectLaborBranches] =
    useState<PerBranchMetricSlices<DirectLaborCostPctData> | null>(null);
  const [productionCostBranches, setProductionCostBranches] =
    useState<PerBranchMetricSlices<ProductionCostPctData> | null>(null);
  const [depreciationBranches, setDepreciationBranches] =
    useState<PerBranchMetricSlices<DepreciationPctData> | null>(null);
  const [oeeBranches, setOeeBranches] =
    useState<PerBranchMetricSlices<OeePctData> | null>(null);
  const [otdBranches, setOtdBranches] =
    useState<PerBranchMetricSlices<OtdPctData> | null>(null);
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
        directLabor !== null ||
        productionCost !== null ||
        depreciation !== null ||
        oee !== null ||
        otd !== null;

      try {
        setError(null);
        setSectionErrors({});

        if (hasPreviousData) setRefreshing(true);
        else setLoading(true);

        const needsBranchIdd = !filters.branch;

        const results = await runParallelWithProgress(
          [
            (signal) => getDirectLaborCostPct(filters, signal),
            (signal) => getProductionCostPct(filters, signal),
            (signal) => getDepreciationPct(filters, signal),
            (signal) => getOverallEquipmentEffectivenessPct(filters, signal),
            (signal) => getOnTimeDeliveryPct(filters, signal),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getDirectLaborCostPct(
                          { ...filters, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.direct_labor_cost_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getProductionCostPct(
                          { ...filters, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.production_cost_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getDepreciationPct(
                          { ...filters, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.depreciation_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getOverallEquipmentEffectivenessPct(
                          { ...filters, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.overall_equipment_effectiveness_pct,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      (branch, branchSignal) =>
                        getOnTimeDeliveryPct(
                          { ...filters, branch },
                          branchSignal ?? signal,
                        ),
                      (data) => data.on_time_delivery_pct,
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
          { key: "directLabor", set: setDirectLabor as (v: unknown) => void },
          {
            key: "productionCost",
            set: setProductionCost as (v: unknown) => void,
          },
          { key: "depreciation", set: setDepreciation as (v: unknown) => void },
          { key: "oee", set: setOee as (v: unknown) => void },
          { key: "otd", set: setOtd as (v: unknown) => void },
        ];

        results.forEach((result, index) => {
          if (index < handlers.length) {
            const { key, set } = handlers[index];
            if (result.status === "fulfilled") {
              set(result.value);
              successCount += 1;
            } else if (!controller.signal.aborted) {
              nextErrors[key] =
                formatProductionApiError(result.reason) ||
                "Erro ao carregar indicador";
            }
            return;
          }

          if (controller.signal.aborted || result.status !== "fulfilled") {
            return;
          }

          const branchIndex = index - handlers.length;
          const branchSetters = [
            setDirectLaborBranches,
            setProductionCostBranches,
            setDepreciationBranches,
            setOeeBranches,
            setOtdBranches,
          ];
          branchSetters[branchIndex]?.(result.value as never);
        });

        if (!controller.signal.aborted && !needsBranchIdd) {
          setDirectLaborBranches(null);
          setProductionCostBranches(null);
          setDepreciationBranches(null);
          setOeeBranches(null);
          setOtdBranches(null);
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
  }, [filters.branch, filters.end_date, filters.start_date, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    directLabor,
    productionCost,
    depreciation,
    oee,
    otd,
    directLaborBranches,
    productionCostBranches,
    depreciationBranches,
    oeeBranches,
    otdBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  };
}
