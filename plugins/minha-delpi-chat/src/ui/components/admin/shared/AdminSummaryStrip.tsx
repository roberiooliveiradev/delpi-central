import type { ReactNode } from "react";

import { AdminKpiGrid } from "./AdminKpiCard";

type AdminSummaryStripProps = {
  ariaLabel: string;
  children: ReactNode;
  isLoading?: boolean;
  className?: string;
};

export function AdminSummaryStrip({
  ariaLabel,
  children,
  isLoading = false,
  className,
}: AdminSummaryStripProps) {
  const rootClass = ["mdc-admin-summary-strip", "mdc-admin-knowledge-summary", className]
    .filter(Boolean)
    .join(" ");

  return (
    <div className={rootClass} role="region" aria-label={ariaLabel} aria-busy={isLoading}>
      <AdminKpiGrid>{children}</AdminKpiGrid>
    </div>
  );
}
