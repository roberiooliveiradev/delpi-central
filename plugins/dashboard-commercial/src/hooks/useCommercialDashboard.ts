import { useCallback, useEffect, useState } from "react";
import {
  getBranchRolTarget,
  getClosingRate,
  getHeadOfficeRolTarget,
  getNewBusinessRolPct,
  getSalesOrderOtd,
} from "../api/commercialApi";
import { formatCommercialApiError } from "../utils/formatCommercialApiError";
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
  closingRate?: string;
  salesOrderOtd?: string;
  newBusinessRol?: string;
};

type UseCommercialDashboardResult = {
  headOfficeRol: RolTargetData | null;
  branchRol: RolTargetData | null;
  closingRate: ClosingRateData | null;
  salesOrderOtd: SalesOrderOtdData | null;
  newBusinessRol: NewBusinessRolPctData | null;
  loading: boolean;
  refreshing: boolean;
  error: string | null;
  sectionErrors: SectionErrors;
  reload: () => void;
};

export function useCommercialDashboard(
  filters: CommercialFilterParams
): UseCommercialDashboardResult {
  const [headOfficeRol, setHeadOfficeRol] = useState<RolTargetData | null>(null);
  const [branchRol, setBranchRol] = useState<RolTargetData | null>(null);
  const [closingRate, setClosingRate] = useState<ClosingRateData | null>(null);
  const [salesOrderOtd, setSalesOrderOtd] = useState<SalesOrderOtdData | null>(null);
  const [newBusinessRol, setNewBusinessRol] = useState<NewBusinessRolPctData | null>(
    null
  );
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [reloadKey, setReloadKey] = useState(0);

  const periodParams = {
    start_date: filters.start_date,
    end_date: filters.end_date,
  };

  const branchParams = filters;

  useEffect(() => {
    const controller = new AbortController();

    async function run() {
      const hasPreviousData =
        headOfficeRol !== null ||
        branchRol !== null ||
        closingRate !== null ||
        salesOrderOtd !== null ||
        newBusinessRol !== null;

      try {
        setError(null);
        setSectionErrors({});

        if (hasPreviousData) setRefreshing(true);
        else setLoading(true);

        const results = await Promise.allSettled([
          getHeadOfficeRolTarget(periodParams, controller.signal),
          getBranchRolTarget(periodParams, controller.signal),
          getClosingRate(branchParams, controller.signal),
          getSalesOrderOtd(branchParams, controller.signal),
          getNewBusinessRolPct(branchParams, controller.signal),
        ]);

        const nextErrors: SectionErrors = {};
        let successCount = 0;

        const handlers: Array<{
          key: keyof SectionErrors;
          set: (v: unknown) => void;
        }> = [
          { key: "headOfficeRol", set: setHeadOfficeRol as (v: unknown) => void },
          { key: "branchRol", set: setBranchRol as (v: unknown) => void },
          { key: "closingRate", set: setClosingRate as (v: unknown) => void },
          { key: "salesOrderOtd", set: setSalesOrderOtd as (v: unknown) => void },
          { key: "newBusinessRol", set: setNewBusinessRol as (v: unknown) => void },
        ];

        results.forEach((result, index) => {
          const { key, set } = handlers[index];
          if (result.status === "fulfilled") {
            set(result.value);
            successCount += 1;
          } else if (!controller.signal.aborted) {
            nextErrors[key] =
              formatCommercialApiError(result.reason) ||
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
    branchParams.branch,
    branchParams.end_date,
    branchParams.start_date,
    reloadKey,
  ]);

  const reload = useCallback(() => {
    setReloadKey((prev) => prev + 1);
  }, []);

  return {
    headOfficeRol,
    branchRol,
    closingRate,
    salesOrderOtd,
    newBusinessRol,
    loading,
    refreshing,
    error,
    sectionErrors,
    reload,
  };
}
