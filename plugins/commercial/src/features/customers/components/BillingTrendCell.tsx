import { Minus, TrendingDown, TrendingUp } from "lucide-react";

import type { CustomerSummary } from "../types/customerSummary";
import {
  billingTrendTitle,
  formatBillingTrendPct,
} from "../utils/billingTrendPresentation";

type BillingTrendCellProps = {
  trend: CustomerSummary["billingTrend"];
  pct: CustomerSummary["billingTrendPct"];
};

export function BillingTrendCell({ trend, pct }: BillingTrendCellProps) {
  if (!trend || trend === "insufficient") {
    return (
      <span className="pva-customers-table__muted" title={billingTrendTitle(trend, pct)}>
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
      className={`pva-billing-trend pva-billing-trend--${trend}`}
      title={title}
    >
      <Icon className="pva-billing-trend__icon" size={16} strokeWidth={2.25} aria-hidden="true" />
      {pctLabel ? <span className="pva-billing-trend__pct">{pctLabel}</span> : null}
      <span className="visually-hidden">{title}</span>
    </span>
  );
}
