import type { AdminAuditLog } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { computeAuditSummary } from "./auditSummary";

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
        hint="Eventos que correspondem aos filtros."
      />
      <AdminKpiCard
        title="Nesta página"
        value={view.pageEvents}
        hint="Linhas exibidas na tabela atual."
      />
      <AdminKpiCard
        title="Ações distintas"
        value={view.uniqueActions}
        hint="Na página carregada."
      />
      <AdminKpiCard
        title="Usuários"
        value={view.uniqueUsers}
        hint={`Na página · ${view.timelineDays} dia(s) na timeline.`}
      />
    </AdminSummaryStrip>
  );
}
