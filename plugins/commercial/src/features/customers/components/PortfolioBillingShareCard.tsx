/**
 * Card KPI share carteira ÷ empresa (KPI-PORTFOLIO-SHARE).
 * Visível só com analytics / team / manage — denominador empresa no BFF.
 */
import { Percent } from "lucide-react";
import { useEffect, useState } from "react";

import { getPortfolioBillingShare } from "../../../api/analyticsApi";
import {
  CommercialDashboardKpiCard,
  CommercialSectionCard,
} from "../../../app/commercialUi";
import { usePortfolioScope } from "../../../app/usePortfolioScope";
import { CM_HELP } from "../../../content/helpTooltips";
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

type PortfolioBillingShareCardProps = {
  sellerId?: string | null;
  startDate?: string;
  endDate?: string;
  branch?: string;
};

export function PortfolioBillingShareCard({
  sellerId,
  startDate,
  endDate,
  branch,
}: PortfolioBillingShareCardProps) {
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

  if (!allowed) return null;

  return (
    <CommercialSectionCard
      title={
        <span title={CM_HELP.customers.portfolioBillingShare}>Share empresa</span>
      }
      className="cm-customers-share-card"
    >
      <CommercialDashboardKpiCard
        title="Share empresa"
        titleHint={CM_HELP.customers.portfolioBillingShare}
        value={error ? "—" : formatSharePct(data?.sharePct)}
        contextLabel={
          error
            ? error
            : data
              ? `${formatCurrency(data.portfolioRol)} / ${formatCurrency(data.companyRol)} · período filtrado`
              : "ROL escopo ÷ ROL empresa"
        }
        icon={<Percent size={22} aria-hidden="true" />}
        loading={loading}
      />
    </CommercialSectionCard>
  );
}
