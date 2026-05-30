import { AlertTriangle, BarChart3, ClipboardList, Target } from "lucide-react";

import { sensoName } from "../constants/audit5s";
import type { AuditDashboardSummary } from "../types/auditDashboard";
import { formatPercent } from "../utils/dates";

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
      <article className="a5s-analytics-kpi">
        <div className="a5s-analytics-kpi__icon" aria-hidden>
          <ClipboardList size={18} />
        </div>
        <div>
          <span className="a5s-analytics-kpi__label">Auditorias no período</span>
          <strong className="a5s-analytics-kpi__value">{summary.audit_count}</strong>
        </div>
      </article>
      <article className="a5s-analytics-kpi">
        <div className="a5s-analytics-kpi__icon" aria-hidden>
          <Target size={18} />
        </div>
        <div>
          <span className="a5s-analytics-kpi__label">{scoreLabel}</span>
          <strong className="a5s-analytics-kpi__value">
            {formatPercent(summary.average_score_pct)}
          </strong>
        </div>
      </article>
      <article className="a5s-analytics-kpi">
        <div className="a5s-analytics-kpi__icon" aria-hidden>
          <BarChart3 size={18} />
        </div>
        <div>
          <span className="a5s-analytics-kpi__label">NC registradas</span>
          <strong className="a5s-analytics-kpi__value">{summary.nc_total}</strong>
          <span className="a5s-analytics-kpi__hint">
            {summary.nc_closed} finalizadas
            {finalizedPct != null ? ` (${finalizedPct}%)` : ""}
          </span>
        </div>
      </article>
      <article className="a5s-analytics-kpi a5s-analytics-kpi--warning">
        <div className="a5s-analytics-kpi__icon" aria-hidden>
          <AlertTriangle size={18} />
        </div>
        <div>
          <span className="a5s-analytics-kpi__label">NC pendentes</span>
          <strong className="a5s-analytics-kpi__value">{summary.nc_open}</strong>
          <span className="a5s-analytics-kpi__hint">
            {summary.nc_overdue > 0 ? `${summary.nc_overdue} em atraso` : "Nenhuma em atraso"}
          </span>
        </div>
      </article>
    </div>
  );
}
