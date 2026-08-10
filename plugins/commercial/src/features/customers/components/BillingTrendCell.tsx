import { Minus, TrendingDown, TrendingUp } from "lucide-react";

import { CommercialDataCellValue } from "../../../app/commercialUi";
import type { CustomerSummary } from "../types/customerSummary";
import {
  billingTrendTitle,
  formatBillingTrendPct,
} from "../utils/billingTrendPresentation";

type BillingTrendCellProps = {
  trend: CustomerSummary["billingTrend"];
  pct: CustomerSummary["billingTrendPct"];
  covered?: boolean;
};

export function BillingTrendCell({ trend, pct, covered = true }: BillingTrendCellProps) {
  if (!covered) {
    return <CommercialDataCellValue value={undefined} present={false} />;
  }

  if (!trend || trend === "insufficient") {
    return (
      <span className="cm-billing-trend cm-billing-trend--muted" title={billingTrendTitle(trend, pct)}>
        —
      </span>
    );
  }

  const pctLabel = formatBillingTrendPct(pct);
  const title = billingTrendTitle(trend, pct);
  const Icon =
    trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;

  return (
    <span
      className={`cm-billing-trend cm-billing-trend--${trend}`}
      title={title}
    >
      <Icon className="cm-billing-trend__icon" size={16} strokeWidth={2.25} aria-hidden="true" />
      {pctLabel ? <span className="cm-billing-trend__pct">{pctLabel}</span> : null}
      <span className="visually-hidden">{title}</span>
    </span>
  );
}
