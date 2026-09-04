import { useCallback, useEffect, useState } from "react";

import {
  getClosingRate,
  getNewBusinessRolPct,
  getNewBusinessRolTarget,
  getOpenPortfolioHorizon,
  getPortfolioBillingShare,
  getRolSummary,
  getSalesOrderOtd,
  getWegRolTarget,
} from "../../../api/analyticsApi";
import type {
  AnalyticsFilterParams,
  ClosingRateData,
  NewBusinessRolPctData,
  OpenPortfolioHorizonData,
  OpenPortfolioSummaryData,
  PortfolioBillingShareData,
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
  /** ROL + meta SI agregada (branch vazio) — só preenchido no consolidado. */
  consolidatedRol: RolTargetData | null;
  headOfficeWegRol: RolTargetData | null;
  branchWegRol: RolTargetData | null;
  consolidatedWegRol: RolTargetData | null;
  headOfficeNewBusinessRol: RolTargetData | null;
  branchNewBusinessRol: RolTargetData | null;
  consolidatedNewBusinessRol: RolTargetData | null;
  closingRate: ClosingRateData | null;
  salesOrderOtd: SalesOrderOtdData | null;
  newBusinessRol: NewBusinessRolPctData | null;
  openPortfolio: OpenPortfolioSummaryData | null;
  openPortfolioHorizon: OpenPortfolioHorizonData | null;
  portfolioBillingShare: PortfolioBillingShareData | null;
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
  const [consolidatedRol, setConsolidatedRol] = useState<RolTargetData | null>(null);
  const [headOfficeWegRol, setHeadOfficeWegRol] = useState<RolTargetData | null>(null);
  const [branchWegRol, setBranchWegRol] = useState<RolTargetData | null>(null);
  const [consolidatedWegRol, setConsolidatedWegRol] = useState<RolTargetData | null>(null);
  const [headOfficeNewBusinessRol, setHeadOfficeNewBusinessRol] =
    useState<RolTargetData | null>(null);
  const [branchNewBusinessRol, setBranchNewBusinessRol] = useState<RolTargetData | null>(null);
  const [consolidatedNewBusinessRol, setConsolidatedNewBusinessRol] =
    useState<RolTargetData | null>(null);
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
  const [openPortfolioHorizon, setOpenPortfolioHorizon] =
    useState<OpenPortfolioHorizonData | null>(null);
  const [portfolioBillingShare, setPortfolioBillingShare] =
    useState<PortfolioBillingShareData | null>(null);
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
    const segmentParams = {
      start_date: filters.start_date,
      end_date: filters.end_date,
      seller_id: filters.seller_id,
      customer_codes: filters.customer_codes,
    };
    const rolParams = {
      start_date: filters.start_date,
      end_date: filters.end_date,
      customer_segment: filters.customer_segment,
      seller_id: filters.seller_id,
      customer_codes: filters.customer_codes,
    };

    void Promise.allSettled([
      getRolSummary({ ...rolParams, branch: "01" }, controller.signal),
      getRolSummary({ ...rolParams, branch: "02" }, controller.signal),
      getWegRolTarget({ ...segmentParams, branch: "01" }, controller.signal),
      getWegRolTarget({ ...segmentParams, branch: "02" }, controller.signal),
      getNewBusinessRolTarget({ ...segmentParams, branch: "01" }, controller.signal),
      getNewBusinessRolTarget({ ...segmentParams, branch: "02" }, controller.signal),
      getClosingRate(filters, controller.signal),
      getSalesOrderOtd(filters, controller.signal),
      getNewBusinessRolPct(filters, controller.signal),
      getPortfolioBillingShare(filters, controller.signal),
      ...(needsBranchIdd
        ? [
            getRolSummary(rolParams, controller.signal),
            getWegRolTarget(segmentParams, controller.signal),
            getNewBusinessRolTarget(segmentParams, controller.signal),
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
        setPortfolioBillingShare(
          results[9].status === "fulfilled"
            ? (results[9].value as PortfolioBillingShareData)
            : null,
        );
        if (needsBranchIdd) {
          setConsolidatedRol(
            results[10]?.status === "fulfilled" ? (results[10].value as RolTargetData) : null,
          );
          setConsolidatedWegRol(
            results[11]?.status === "fulfilled" ? (results[11].value as RolTargetData) : null,
          );
          setConsolidatedNewBusinessRol(
            results[12]?.status === "fulfilled" ? (results[12].value as RolTargetData) : null,
          );
          const crBranches = results[13];
          const otdBranches = results[14];
          const nbBranches = results[15];
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
          setConsolidatedRol(null);
          setConsolidatedWegRol(null);
          setConsolidatedNewBusinessRol(null);
          setClosingRateBranches(null);
          setSalesOrderOtdBranches(null);
          setNewBusinessRolBranches(null);
        }
        const core = results.slice(0, 10);
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
    filters.customer_codes,
    reloadKey,
  ]);

  // Snapshot carteira + horizon — 1× TOTVS no BFF; independente do período.
  useEffect(() => {
    const controller = new AbortController();
    setOpenPortfolioLoading(true);
    setOpenPortfolioError(null);
    void getOpenPortfolioHorizon(
      { seller_id: filters.seller_id, customer_codes: filters.customer_codes },
      controller.signal,
    )
      .then((data) => {
        if (controller.signal.aborted) return;
        setOpenPortfolioHorizon(data);
        setOpenPortfolio({
          openValue: data.totals.openValue,
          openLineCount: data.totals.openLineCount,
          asOf: data.asOf,
          nature: "open_order_value",
        });
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setOpenPortfolio(null);
        setOpenPortfolioHorizon(null);
        setOpenPortfolioError(
          err instanceof Error ? err.message : "Erro ao carregar carteira em aberto.",
        );
      })
      .finally(() => {
        if (!controller.signal.aborted) setOpenPortfolioLoading(false);
      });
    return () => controller.abort();
  }, [filters.seller_id, filters.customer_codes, reloadKey]);

  return {
    headOfficeRol,
    branchRol,
    consolidatedRol,
    headOfficeWegRol,
    branchWegRol,
    consolidatedWegRol,
    headOfficeNewBusinessRol,
    branchNewBusinessRol,
    consolidatedNewBusinessRol,
    closingRate,
    salesOrderOtd,
    newBusinessRol,
    openPortfolio,
    openPortfolioHorizon,
    portfolioBillingShare,
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
