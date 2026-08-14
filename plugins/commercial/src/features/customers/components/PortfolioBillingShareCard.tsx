/**
 * Card KPI share carteira ÷ empresa (KPI-PORTFOLIO-SHARE).
 * Thin wrapper — lógica de fetch em `usePortfolioBillingShare`.
 */
import { Percent } from "lucide-react";

import {
  CommercialDashboardKpiCard,
  CommercialSectionCard,
} from "../../../app/commercialUi";
import { CM_HELP } from "../../../content/helpTooltips";
import {
  formatSharePct,
  usePortfolioBillingShare,
} from "../hooks/usePortfolioBillingShare";

export {
  canViewPortfolioBillingShare,
  formatSharePct,
} from "../hooks/usePortfolioBillingShare";

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
  const { allowed, data, loading, error, contextLabel } = usePortfolioBillingShare({
    sellerId,
    startDate,
    endDate,
    branch,
  });

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
        contextLabel={contextLabel}
        icon={<Percent size={22} aria-hidden="true" />}
        loading={loading}
      />
    </CommercialSectionCard>
  );
}
