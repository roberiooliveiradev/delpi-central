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
  loading: boolean;
  refreshing: boolean;
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
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);

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

        const results = await Promise.allSettled([
          getDirectLaborCostPct(filters, controller.signal),
          getProductionCostPct(filters, controller.signal),
          getDepreciationPct(filters, controller.signal),
          getOverallEquipmentEffectivenessPct(filters, controller.signal),
          getOnTimeDeliveryPct(filters, controller.signal),
        ]);

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
          const { key, set } = handlers[index];
          if (result.status === "fulfilled") {
            set(result.value);
            successCount += 1;
          } else if (!controller.signal.aborted) {
            nextErrors[key] =
              formatProductionApiError(result.reason) ||
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
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  };
}
