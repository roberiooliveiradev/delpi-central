import type { AdminAuditLog } from "../../../../data/api/adminTypes";

import { computeAuditSummary } from "./auditSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

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
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo da auditoria"
      aria-busy={isLoading}
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>Total (filtro)</h3>
          <strong>{view.total}</strong>
          <p>Eventos que correspondem aos filtros.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Nesta página</h3>
          <strong>{view.pageEvents}</strong>
          <p>Linhas exibidas na tabela atual.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Ações distintas</h3>
          <strong>{view.uniqueActions}</strong>
          <p>Na página carregada.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Usuários</h3>
          <strong>{view.uniqueUsers}</strong>
          <p>Na página · {view.timelineDays} dia(s) na timeline.</p>
        </article>
      </div>
    </div>
  );
}
