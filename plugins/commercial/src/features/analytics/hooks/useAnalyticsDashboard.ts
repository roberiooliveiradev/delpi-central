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

    const isConsolidatedView = !filters.branch?.trim();
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

    const settledValue = <T,>(
      result: PromiseSettledResult<T> | undefined,
    ): T | null => (result?.status === "fulfilled" ? result.value : null);

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
      // Meta consolidada SI (branch omitido) — sempre buscar na visão «Todas»;
      // índices nomeados abaixo evitam regressão ao reordenar o allSettled.
      ...(isConsolidatedView
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
        const [
          rol01,
          rol02,
          weg01,
          weg02,
          nb01,
          nb02,
          closing,
          otd,
          newBusinessPct,
          billingShare,
          rolConsolidated,
          wegConsolidated,
          nbConsolidated,
          closingBranches,
          otdBranches,
          nbBranches,
        ] = results;

        setHeadOfficeRol(settledValue(rol01));
        setBranchRol(settledValue(rol02));
        setHeadOfficeWegRol(settledValue(weg01));
        setBranchWegRol(settledValue(weg02));
        setHeadOfficeNewBusinessRol(settledValue(nb01));
        setBranchNewBusinessRol(settledValue(nb02));
        setClosingRate(settledValue(closing));
        setSalesOrderOtd(settledValue(otd));
        setNewBusinessRol(settledValue(newBusinessPct));
        setPortfolioBillingShare(
          settledValue(billingShare) as PortfolioBillingShareData | null,
        );
        if (isConsolidatedView) {
          setConsolidatedRol(settledValue(rolConsolidated) as RolTargetData | null);
          setConsolidatedWegRol(settledValue(wegConsolidated) as RolTargetData | null);
          setConsolidatedNewBusinessRol(
            settledValue(nbConsolidated) as RolTargetData | null,
          );
          setClosingRateBranches(
            settledValue(closingBranches) as PerBranchMetricSlices<ClosingRateData> | null,
          );
          setSalesOrderOtdBranches(
            settledValue(otdBranches) as PerBranchMetricSlices<SalesOrderOtdData> | null,
          );
          setNewBusinessRolBranches(
            settledValue(nbBranches) as PerBranchMetricSlices<NewBusinessRolPctData> | null,
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
