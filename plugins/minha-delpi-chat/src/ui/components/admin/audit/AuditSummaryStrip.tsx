import type { AdminAuditLog } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { computeAuditSummary } from "./auditSummary";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type AuditSummaryStripProps = {
  logs: AdminAuditLog[];
  total?: number;
  timelineDayCount?: number;
  isLoading?: boolean;
};

export function AuditSummaryStrip({
  logs,
  total,
  timelineDayCount = 0,
  isLoading = false,
}: AuditSummaryStripProps) {
  const view = computeAuditSummary(logs, total, timelineDayCount);

  return (
    <AdminSummaryStrip ariaLabel="Resumo da auditoria" isLoading={isLoading}>
      <AdminKpiCard
        title="Total (filtro)"
        value={view.total}
        hint={ADMIN_HELP.kpis.audit.matching}
      />
      <AdminKpiCard
        title="Nesta página"
        value={view.pageEvents}
        hint={ADMIN_HELP.kpis.audit.pageRows}
      />
      <AdminKpiCard
        title="Ações distintas"
        value={view.uniqueActions}
        hint={ADMIN_HELP.kpis.audit.pageEvents}
      />
      <AdminKpiCard
        title="Usuários"
        value={view.uniqueUsers}
        hint={`${ADMIN_HELP.kpis.audit.timeline} ${view.timelineDays} dia(s).`}
      />
    </AdminSummaryStrip>
  );
}
