import { useCallback, useEffect, useState } from "react";

import {
  getBranchRolTarget,
  getClosingRate,
  getHeadOfficeRolTarget,
  getNewBusinessRolPct,
  getSalesOrderOtd,
} from "../../../api/analyticsApi";
import type {
  ClosingRateData,
  AnalyticsFilterParams,
  NewBusinessRolPctData,
  RolTargetData,
  SalesOrderOtdData,
} from "../../../types/analytics";

type AnalyticsDashboardState = {
  headOfficeRol: RolTargetData | null;
  branchRol: RolTargetData | null;
  closingRate: ClosingRateData | null;
  salesOrderOtd: SalesOrderOtdData | null;
  newBusinessRol: NewBusinessRolPctData | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useAnalyticsDashboard(filters: AnalyticsFilterParams): AnalyticsDashboardState {
  const [headOfficeRol, setHeadOfficeRol] = useState<RolTargetData | null>(null);
  const [branchRol, setBranchRol] = useState<RolTargetData | null>(null);
  const [closingRate, setClosingRate] = useState<ClosingRateData | null>(null);
  const [salesOrderOtd, setSalesOrderOtd] = useState<SalesOrderOtdData | null>(null);
  const [newBusinessRol, setNewBusinessRol] = useState<NewBusinessRolPctData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((v) => v + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    void Promise.allSettled([
      getHeadOfficeRolTarget(filters, controller.signal),
      getBranchRolTarget(filters, controller.signal),
      getClosingRate(filters, controller.signal),
      getSalesOrderOtd(filters, controller.signal),
      getNewBusinessRolPct(filters, controller.signal),
    ])
      .then((results) => {
        if (controller.signal.aborted) return;
        const [ho, br, cr, otd, nb] = results;
        setHeadOfficeRol(ho.status === "fulfilled" ? ho.value : null);
        setBranchRol(br.status === "fulfilled" ? br.value : null);
        setClosingRate(cr.status === "fulfilled" ? cr.value : null);
        setSalesOrderOtd(otd.status === "fulfilled" ? otd.value : null);
        setNewBusinessRol(nb.status === "fulfilled" ? nb.value : null);
        const firstError = results.find((r) => r.status === "rejected") as
          | PromiseRejectedResult
          | undefined;
        if (firstError && results.every((r) => r.status === "rejected")) {
          setError(
            firstError.reason instanceof Error
              ? firstError.reason.message
              : "Erro ao carregar KPIs de gestão.",
          );
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [
    filters.start_date,
    filters.end_date,
    filters.branch,
    filters.customer_segment,
    reloadKey,
  ]);

  return {
    headOfficeRol,
    branchRol,
    closingRate,
    salesOrderOtd,
    newBusinessRol,
    loading,
    error,
    reload,
  };
}
