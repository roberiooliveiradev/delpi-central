import type { ReactNode } from "react";
import { delpiUiClass } from "@delpi/plugin-ui/index";

import { AdminKpiGrid } from "./AdminKpiCard";

type AdminSummaryStripProps = {
  ariaLabel: string;
  children: ReactNode;
  isLoading?: boolean;
  className?: string;
};

/**
 * Faixa de KPIs — dual-class com tokens do kit (convergência gradual).
 */
export function AdminSummaryStrip({
  ariaLabel,
  children,
  isLoading = false,
  className,
}: AdminSummaryStripProps) {
  const rootClass = [
    delpiUiClass("mdc-admin-summary-strip", "delpi-ui-kpi-grid"),
    "mdc-admin-knowledge-summary",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} role="region" aria-label={ariaLabel} aria-busy={isLoading}>
      <AdminKpiGrid>{children}</AdminKpiGrid>
    </div>
  );
}
