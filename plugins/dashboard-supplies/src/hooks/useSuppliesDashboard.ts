import { useCallback, useEffect, useState } from "react";
import {
  getCpv,
  getInventoryTurnover,
  getNegotiationSavings,
  getOtd,
  getStockValueSummary,
} from "../api/suppliesApi";
import type {
  CpvData,
  InventoryTurnoverData,
  NegotiationSavingsData,
  OtdData,
  StockValueData,
  SuppliesFilterParams,
} from "../types/supplies";
import { formatSuppliesApiError } from "../utils/formatSuppliesApiError";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../utils/goalDisplay";
import type { CpvSummary, InventoryTurnoverSummary, NegotiationSavingsSummary, OtdSummary, StockValueSummary } from "../types/supplies";
import {
  EMPTY_REQUEST_PROGRESS,
  runParallelWithProgress,
  type RequestProgress,
} from "../utils/loadingProgress";

type SectionErrors = {
  cpv?: string;
  otd?: string;
  stockValue?: string;
  inventoryTurnover?: string;
  negotiationSavings?: string;
};

type UseSuppliesDashboardParams = {
  periodParams: SuppliesFilterParams;
  stockParams: SuppliesFilterParams;
};

type UseSuppliesDashboardResult = {
  cpv: CpvData | null;
  otd: OtdData | null;
  stockValue: StockValueData | null;
  inventoryTurnover: InventoryTurnoverData | null;
  negotiationSavings: NegotiationSavingsData | null;
  cpvBranches: PerBranchMetricSlices<CpvSummary> | null;
  otdBranches: PerBranchMetricSlices<OtdSummary> | null;
  stockValueBranches: PerBranchMetricSlices<StockValueSummary> | null;
  inventoryTurnoverBranches: PerBranchMetricSlices<InventoryTurnoverSummary> | null;
  negotiationSavingsBranches: PerBranchMetricSlices<NegotiationSavingsSummary> | null;
  loading: boolean;
  refreshing: boolean;
  requestProgress: RequestProgress;
  error: string | null;
  sectionErrors: SectionErrors;
  reload: () => void;
};

export function useSuppliesDashboard({
  periodParams,
  stockParams,
}: UseSuppliesDashboardParams): UseSuppliesDashboardResult {
  const [cpv, setCpv] = useState<CpvData | null>(null);
  const [otd, setOtd] = useState<OtdData | null>(null);
  const [stockValue, setStockValue] = useState<StockValueData | null>(null);
  const [inventoryTurnover, setInventoryTurnover] =
    useState<InventoryTurnoverData | null>(null);
  const [negotiationSavings, setNegotiationSavings] =
    useState<NegotiationSavingsData | null>(null);
  const [cpvBranches, setCpvBranches] =
    useState<PerBranchMetricSlices<CpvSummary> | null>(null);
  const [otdBranches, setOtdBranches] =
    useState<PerBranchMetricSlices<OtdSummary> | null>(null);
  const [stockValueBranches, setStockValueBranches] =
    useState<PerBranchMetricSlices<StockValueSummary> | null>(null);
  const [inventoryTurnoverBranches, setInventoryTurnoverBranches] =
    useState<PerBranchMetricSlices<InventoryTurnoverSummary> | null>(null);
  const [negotiationSavingsBranches, setNegotiationSavingsBranches] =
    useState<PerBranchMetricSlices<NegotiationSavingsSummary> | null>(null);
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
        cpv !== null ||
        otd !== null ||
        stockValue !== null ||
        inventoryTurnover !== null ||
        negotiationSavings !== null;

      try {
        setError(null);
        setSectionErrors({});

        if (hasPreviousData) setRefreshing(true);
        else setLoading(true);

        const needsBranchIdd = !periodParams.branch;

        const results = await runParallelWithProgress(
          [
            (signal) => getCpv(periodParams, signal),
            (signal) => getOtd(periodParams, signal),
            (signal) => getStockValueSummary(stockParams, signal),
            (signal) => getInventoryTurnover(periodParams, signal),
            (signal) =>
              getNegotiationSavings(
                {
                  start_date: periodParams.start_date,
                  end_date: periodParams.end_date,
                  branch: periodParams.branch,
                },
                signal
              ),
            ...(needsBranchIdd
              ? [
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      async (branch, branchSignal) =>
                        (await getCpv(
                          { ...periodParams, branch },
                          branchSignal ?? signal,
                        )).summary,
                      (summary) => summary.cpv_percentage,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      async (branch, branchSignal) =>
                        (await getOtd(
                          { ...periodParams, branch },
                          branchSignal ?? signal,
                        )).summary,
                      (summary) => summary.otd_percentage,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      async (branch, branchSignal) =>
                        (await getStockValueSummary(
                          { ...stockParams, branch },
                          branchSignal ?? signal,
                        )).summary,
                      (summary) => summary.total_stock_value,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      async (branch, branchSignal) =>
                        (await getInventoryTurnover(
                          { ...periodParams, branch },
                          branchSignal ?? signal,
                        )).summary,
                      (summary) => summary.inventory_turnover_times,
                      signal,
                    ),
                  (signal: AbortSignal) =>
                    fetchPerBranchMetricSlices(
                      async (branch, branchSignal) =>
                        (
                          await getNegotiationSavings(
                            {
                              start_date: periodParams.start_date,
                              end_date: periodParams.end_date,
                              branch,
                            },
                            branchSignal ?? signal,
                          )
                        ).summary,
                      (summary) => summary.total_savings,
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
          { key: "cpv", set: setCpv as (v: unknown) => void },
          { key: "otd", set: setOtd as (v: unknown) => void },
          { key: "stockValue", set: setStockValue as (v: unknown) => void },
          {
            key: "inventoryTurnover",
            set: setInventoryTurnover as (v: unknown) => void,
          },
          {
            key: "negotiationSavings",
            set: setNegotiationSavings as (v: unknown) => void,
          },
        ];

        results.forEach((result, index) => {
          if (index < handlers.length) {
            const { key, set } = handlers[index];
            if (result.status === "fulfilled") {
              set(result.value);
              successCount += 1;
            } else if (!controller.signal.aborted) {
              nextErrors[key] =
                formatSuppliesApiError(result.reason) ||
                "Erro ao carregar indicador";
            }
            return;
          }

          if (controller.signal.aborted || result.status !== "fulfilled") {
            return;
          }

          const branchSetters = [
            setCpvBranches,
            setOtdBranches,
            setStockValueBranches,
            setInventoryTurnoverBranches,
            setNegotiationSavingsBranches,
          ];
          branchSetters[index - handlers.length]?.(result.value as never);
        });

        if (!controller.signal.aborted && !needsBranchIdd) {
          setCpvBranches(null);
          setOtdBranches(null);
          setStockValueBranches(null);
          setInventoryTurnoverBranches(null);
          setNegotiationSavingsBranches(null);
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
    periodParams.branch,
    periodParams.end_date,
    periodParams.location,
    periodParams.start_date,
    stockParams.branch,
    stockParams.end_date,
    stockParams.location,
    stockParams.start_date,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    cpv,
    otd,
    stockValue,
    inventoryTurnover,
    negotiationSavings,
    cpvBranches,
    otdBranches,
    stockValueBranches,
    inventoryTurnoverBranches,
    negotiationSavingsBranches,
    loading,
    refreshing,
    requestProgress,
    error,
    sectionErrors,
    reload,
  };
}
