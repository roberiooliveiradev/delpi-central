import { AlertTriangle, BarChart3, ClipboardList, Target } from "lucide-react";

import { sensoName } from "../constants/audit5s";
import type { AuditDashboardSummary } from "../types/auditDashboard";
import { formatPercent } from "../utils/dates";
import { KpiCard } from "./KpiCard";

type Props = {
  summary: AuditDashboardSummary;
};

export function AuditDashboardKpis({ summary }: Props) {
  const finalizedPct =
    summary.nc_total > 0
      ? Math.round((summary.nc_closed / summary.nc_total) * 100)
      : null;
  const sensoLabel =
    summary.filtered_senso_order != null
      ? sensoName(summary.filtered_senso_order, summary.filtered_senso_name ?? undefined)
      : null;
  const scoreLabel = sensoLabel ? `Nota média — ${sensoLabel}` : "Nota média geral";

  return (
    <div className="a5s-analytics-kpis">
      <KpiCard
        title="Auditorias no período"
        value={String(summary.audit_count)}
        icon={<ClipboardList size={22} />}
      />
      <KpiCard
        title={scoreLabel}
        value={formatPercent(summary.average_score_pct)}
        icon={<Target size={22} />}
      />
      <KpiCard
        title="NC registradas"
        value={String(summary.nc_total)}
        subtitle={`${summary.nc_closed} finalizadas${finalizedPct != null ? ` (${finalizedPct}%)` : ""}`}
        icon={<BarChart3 size={22} />}
      />
      <KpiCard
        title="NC pendentes"
        value={String(summary.nc_open)}
        subtitle={
          summary.nc_overdue > 0 ? `${summary.nc_overdue} em atraso` : "Nenhuma em atraso"
        }
        variant="warning"
        icon={<AlertTriangle size={22} />}
      />
    </div>
  );
}
