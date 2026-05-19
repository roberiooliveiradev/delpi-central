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
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);

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

        const results = await Promise.allSettled([
          getRol(apiParams, controller.signal),
          getEbitdaPct(apiParams, controller.signal),
          getFixedCostPct(apiParams, controller.signal),
          getPmr(apiParams, controller.signal),
        ]);

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
          const { key, set } = handlers[index];
          if (result.status === "fulfilled") {
            set(result.value);
            successCount += 1;
          } else if (!controller.signal.aborted) {
            nextErrors[key] =
              formatFinancialApiError(result.reason) ||
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
  }, [apiParams.branch, apiParams.end_date, apiParams.start_date, reloadKey]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    rol,
    ebitda,
    fixedCost,
    pmr,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  };
}
