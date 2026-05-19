import { useCallback, useEffect, useState } from "react";
import {
  getCpv,
  getInventoryTurnover,
  getOtd,
  getStockValue,
} from "../api/suppliesApi";
import type {
  CpvData,
  InventoryTurnoverData,
  OtdData,
  StockValueData,
  SuppliesFilterParams,
} from "../types/supplies";
import { formatSuppliesApiError } from "../utils/formatSuppliesApiError";

type SectionErrors = {
  cpv?: string;
  otd?: string;
  stockValue?: string;
  inventoryTurnover?: string;
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
  loading: boolean;
  refreshing: boolean;
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
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousData =
        cpv !== null ||
        otd !== null ||
        stockValue !== null ||
        inventoryTurnover !== null;

      try {
        setError(null);
        setSectionErrors({});

        if (hasPreviousData) setRefreshing(true);
        else setLoading(true);

        const results = await Promise.allSettled([
          getCpv(periodParams, controller.signal),
          getOtd(periodParams, controller.signal),
          getStockValue(stockParams, controller.signal),
          getInventoryTurnover(periodParams, controller.signal),
        ]);

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
        ];

        results.forEach((result, index) => {
          const { key, set } = handlers[index];
          if (result.status === "fulfilled") {
            set(result.value);
            successCount += 1;
          } else if (!controller.signal.aborted) {
            nextErrors[key] =
              formatSuppliesApiError(result.reason) ||
              "Erro ao carregar indicador";
          }
        });

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
    stockParams.location,
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
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  };
}
