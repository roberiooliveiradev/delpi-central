import type { AdminSecuritySummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { buildSecuritySummaryView } from "./securitySummary";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type SecuritySummaryStripProps = {
  summary: AdminSecuritySummary | null | undefined;
  isLoading?: boolean;
};

export function SecuritySummaryStrip({
  summary,
  isLoading = false,
}: SecuritySummaryStripProps) {
  const view = buildSecuritySummaryView(summary);
  const windowLabel = summary?.windowHours ?? 24;

  return (
    <AdminSummaryStrip
      ariaLabel="Resumo de segurança operacional"
      isLoading={isLoading}
    >
      <AdminKpiCard
        title={`Bloqueios (${windowLabel}h)`}
        value={view.blocked}
        hint={ADMIN_HELP.kpis.security.blocked}
      />
      <AdminKpiCard
        title={`Sinalizados (${windowLabel}h)`}
        value={view.flagged}
        hint={ADMIN_HELP.kpis.security.events}
      />
      <AdminKpiCard
        title={`Scans admin (${windowLabel}h)`}
        value={view.scanned}
        hint={ADMIN_HELP.kpis.security.scans}
      />
      <AdminKpiCard title="Total eventos" value={view.totalEvents} hint={ADMIN_HELP.kpis.security.total} />
    </AdminSummaryStrip>
  );
}
