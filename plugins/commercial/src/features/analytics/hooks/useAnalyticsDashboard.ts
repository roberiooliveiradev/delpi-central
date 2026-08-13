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
  getOpenPortfolioSummary,
  getSalesOrderOtd,
} from "../../../api/analyticsApi";
import type {
  AnalyticsFilterParams,
  ClosingRateData,
  NewBusinessRolPctData,
  OpenPortfolioSummaryData,
  RolTargetData,
  SalesOrderOtdData,
} from "../../../types/analytics";
import {
  fetchPerBranchMetricSlices,
  type PerBranchMetricSlices,
} from "../../overview/goalDisplay";

type AnalyticsDashboardState = {
  headOfficeRol: RolTargetData | null;
  branchRol: RolTargetData | null;
  headOfficeWegRol: RolTargetData | null;
  branchWegRol: RolTargetData | null;
  headOfficeNewBusinessRol: RolTargetData | null;
  branchNewBusinessRol: RolTargetData | null;
  closingRate: ClosingRateData | null;
  salesOrderOtd: SalesOrderOtdData | null;
  newBusinessRol: NewBusinessRolPctData | null;
  openPortfolio: OpenPortfolioSummaryData | null;
  openPortfolioLoading: boolean;
  openPortfolioError: string | null;
  closingRateBranches: PerBranchMetricSlices<ClosingRateData> | null;
  salesOrderOtdBranches: PerBranchMetricSlices<SalesOrderOtdData> | null;
  newBusinessRolBranches: PerBranchMetricSlices<NewBusinessRolPctData> | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
};

export function useAnalyticsDashboard(filters: AnalyticsFilterParams): AnalyticsDashboardState {
  const [headOfficeRol, setHeadOfficeRol] = useState<RolTargetData | null>(null);
  const [branchRol, setBranchRol] = useState<RolTargetData | null>(null);
  const [headOfficeWegRol, setHeadOfficeWegRol] = useState<RolTargetData | null>(null);
  const [branchWegRol, setBranchWegRol] = useState<RolTargetData | null>(null);
  const [headOfficeNewBusinessRol, setHeadOfficeNewBusinessRol] =
    useState<RolTargetData | null>(null);
  const [branchNewBusinessRol, setBranchNewBusinessRol] = useState<RolTargetData | null>(null);
  const [closingRate, setClosingRate] = useState<ClosingRateData | null>(null);
  const [salesOrderOtd, setSalesOrderOtd] = useState<SalesOrderOtdData | null>(null);
  const [newBusinessRol, setNewBusinessRol] = useState<NewBusinessRolPctData | null>(null);
  const [closingRateBranches, setClosingRateBranches] =
    useState<PerBranchMetricSlices<ClosingRateData> | null>(null);
  const [salesOrderOtdBranches, setSalesOrderOtdBranches] =
    useState<PerBranchMetricSlices<SalesOrderOtdData> | null>(null);
  const [newBusinessRolBranches, setNewBusinessRolBranches] =
    useState<PerBranchMetricSlices<NewBusinessRolPctData> | null>(null);
  const [openPortfolio, setOpenPortfolio] = useState<OpenPortfolioSummaryData | null>(null);
  const [openPortfolioLoading, setOpenPortfolioLoading] = useState(true);
  const [openPortfolioError, setOpenPortfolioError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((v) => v + 1), []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    const needsBranchIdd = !filters.branch;
    const segmentParams: AnalyticsFilterParams = {
      start_date: filters.start_date,
      end_date: filters.end_date,
      branch: filters.branch,
      seller_id: filters.seller_id,
    };

    void Promise.allSettled([
      getHeadOfficeRolTarget(filters, controller.signal),
      getBranchRolTarget(filters, controller.signal),
      getHeadOfficeWegRolTarget(segmentParams, controller.signal),
      getBranchWegRolTarget(segmentParams, controller.signal),
      getHeadOfficeNewBusinessRolTarget(segmentParams, controller.signal),
      getBranchNewBusinessRolTarget(segmentParams, controller.signal),
      getClosingRate(filters, controller.signal),
      getSalesOrderOtd(filters, controller.signal),
      getNewBusinessRolPct(filters, controller.signal),
      ...(needsBranchIdd
        ? [
            fetchPerBranchMetricSlices(
              (branch, branchSignal) =>
                getClosingRate({ ...filters, branch }, branchSignal ?? controller.signal),
              (data) => data.sales_conversion_rate_pct,
              controller.signal,
            ),
            fetchPerBranchMetricSlices(
              (branch, branchSignal) =>
                getSalesOrderOtd({ ...filters, branch }, branchSignal ?? controller.signal),
              (data) => data.sales_order_otd_pct,
              controller.signal,
            ),
            fetchPerBranchMetricSlices(
              (branch, branchSignal) =>
                getNewBusinessRolPct({ ...filters, branch }, branchSignal ?? controller.signal),
              (data) => data.new_business_rol_pct,
              controller.signal,
            ),
          ]
        : []),
    ])
      .then((results) => {
        if (controller.signal.aborted) return;
        setHeadOfficeRol(results[0].status === "fulfilled" ? results[0].value : null);
        setBranchRol(results[1].status === "fulfilled" ? results[1].value : null);
        setHeadOfficeWegRol(results[2].status === "fulfilled" ? results[2].value : null);
        setBranchWegRol(results[3].status === "fulfilled" ? results[3].value : null);
        setHeadOfficeNewBusinessRol(
          results[4].status === "fulfilled" ? results[4].value : null,
        );
        setBranchNewBusinessRol(results[5].status === "fulfilled" ? results[5].value : null);
        setClosingRate(results[6].status === "fulfilled" ? results[6].value : null);
        setSalesOrderOtd(results[7].status === "fulfilled" ? results[7].value : null);
        setNewBusinessRol(results[8].status === "fulfilled" ? results[8].value : null);
        if (needsBranchIdd) {
          const crBranches = results[9];
          const otdBranches = results[10];
          const nbBranches = results[11];
          setClosingRateBranches(
            crBranches?.status === "fulfilled"
              ? (crBranches.value as PerBranchMetricSlices<ClosingRateData>)
              : null,
          );
          setSalesOrderOtdBranches(
            otdBranches?.status === "fulfilled"
              ? (otdBranches.value as PerBranchMetricSlices<SalesOrderOtdData>)
              : null,
          );
          setNewBusinessRolBranches(
            nbBranches?.status === "fulfilled"
              ? (nbBranches.value as PerBranchMetricSlices<NewBusinessRolPctData>)
              : null,
          );
        } else {
          setClosingRateBranches(null);
          setSalesOrderOtdBranches(null);
          setNewBusinessRolBranches(null);
        }
        const core = results.slice(0, 9);
        const firstError = core.find((r) => r.status === "rejected") as
          | PromiseRejectedResult
          | undefined;
        if (firstError && core.every((r) => r.status === "rejected")) {
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
    filters.seller_id,
    reloadKey,
  ]);

  // Snapshot carteira — independente do período (só escopo seller_id).
  useEffect(() => {
    const controller = new AbortController();
    setOpenPortfolioLoading(true);
    setOpenPortfolioError(null);
    void getOpenPortfolioSummary({ seller_id: filters.seller_id }, controller.signal)
      .then((data) => {
        if (!controller.signal.aborted) setOpenPortfolio(data);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOpenPortfolio(null);
        setOpenPortfolioError(
          err instanceof Error ? err.message : "Erro ao carregar carteira em aberto.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setOpenPortfolioLoading(false);
      });
    return () => controller.abort();
  }, [filters.seller_id, reloadKey]);

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
    openPortfolio,
    openPortfolioLoading,
    openPortfolioError,
    closingRateBranches,
    salesOrderOtdBranches,
    newBusinessRolBranches,
    loading,
    error,
    reload,
  };
}
