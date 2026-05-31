import type { AdminSecuritySummary } from "../../../../data/api/adminTypes";

import { buildSecuritySummaryView } from "./securitySummary";

import "../knowledge/KnowledgeSummaryStrip.css";

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
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo de segurança operacional"
      aria-busy={isLoading}
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>Bloqueios ({windowLabel}h)</h3>
          <strong>{view.blocked}</strong>
          <p>Mensagens barradas no chat.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Sinalizados ({windowLabel}h)</h3>
          <strong>{view.flagged}</strong>
          <p>Registrados na auditoria.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Scans admin ({windowLabel}h)</h3>
          <strong>{view.scanned}</strong>
          <p>Testes pelo painel.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Total eventos</h3>
          <strong>{view.totalEvents}</strong>
          <p>Na janela selecionada.</p>
        </article>
      </div>
    </div>
  );
}
