/**
 * Share carteira ÷ empresa (KPI-PORTFOLIO-SHARE) — fetch + permissão.
 */
import { useEffect, useState } from "react";

import { getPortfolioBillingShare } from "../../../api/analyticsApi";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import type { PortfolioBillingShareData } from "../../../types/analytics";
import { formatCurrency } from "../../../utils/format";
import {
  DEFAULT_BILLING_SERIES_PRESET,
  periodRangeFromBillingPreset,
} from "../utils/billingSeriesPeriod";

export function canViewPortfolioBillingShare(capabilities: {
  canViewAnalytics: boolean;
  canViewAccountsTeam: boolean;
  canManagePortfolios: boolean;
}): boolean {
  return (
    capabilities.canViewAnalytics ||
    capabilities.canViewAccountsTeam ||
    capabilities.canManagePortfolios
  );
}

export function formatSharePct(sharePct: number | null | undefined): string {
  if (sharePct == null || Number.isNaN(sharePct)) return "—";
  return `${sharePct.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}%`;
}

export type UsePortfolioBillingShareOptions = {
  sellerId?: string | null;
  startDate?: string;
  endDate?: string;
  branch?: string;
};

export type UsePortfolioBillingShareResult = {
  allowed: boolean;
  data: PortfolioBillingShareData | null;
  loading: boolean;
  error: string | null;
  contextLabel: string;
  shareLabel: string;
};

export function usePortfolioBillingShare(
  options: UsePortfolioBillingShareOptions = {},
): UsePortfolioBillingShareResult {
  const { sellerId, startDate, endDate, branch } = options;
  const { canViewAnalytics, canViewAccountsTeam, canManagePortfolios } =
    usePortfolioScope();
  const allowed = canViewPortfolioBillingShare({
    canViewAnalytics,
    canViewAccountsTeam,
    canManagePortfolios,
  });

  const defaultRange = periodRangeFromBillingPreset(DEFAULT_BILLING_SERIES_PRESET);
  const resolvedStart = startDate || defaultRange.startDate;
  const resolvedEnd = endDate || defaultRange.endDate;

  const [data, setData] = useState<PortfolioBillingShareData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!allowed) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    void getPortfolioBillingShare(
      {
        start_date: resolvedStart,
        end_date: resolvedEnd,
        branch: branch || undefined,
        seller_id: sellerId?.trim() || undefined,
      },
      controller.signal,
    )
      .then((payload) => {
        if (controller.signal.aborted) return;
        setData(payload);
      })
      .catch((err: unknown) => {
        if (controller.signal.aborted) return;
        setData(null);
        setError(err instanceof Error ? err.message : "Erro ao carregar share.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [allowed, resolvedStart, resolvedEnd, branch, sellerId]);

  return {
    allowed,
    data,
    loading,
    error,
    shareLabel: error ? "—" : loading && !data ? "…" : formatSharePct(data?.sharePct),
    contextLabel: error
      ? error
      : data
        ? `${formatCurrency(data.portfolioRol)} / ${formatCurrency(data.companyRol)} · período filtrado`
        : "ROL escopo ÷ ROL empresa",
  };
}
