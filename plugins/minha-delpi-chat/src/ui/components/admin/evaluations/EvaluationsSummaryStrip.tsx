import type { AdminResponseEvaluationSummary } from "../../../../data/api/adminTypes";

import { buildEvaluationsSummaryView } from "./evaluationsSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

type EvaluationsSummaryStripProps = {
  summary: AdminResponseEvaluationSummary | null | undefined;
  isLoading?: boolean;
};

export function EvaluationsSummaryStrip({
  summary,
  isLoading = false,
}: EvaluationsSummaryStripProps) {
  const view = buildEvaluationsSummaryView(summary);

  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo de avaliações de respostas"
      aria-busy={isLoading}
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>Total</h3>
          <strong>{view.total}</strong>
          <p>Avaliações registradas.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Média</h3>
          <strong>{view.averageScore}</strong>
          <p>Nota média (1–5).</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Úteis</h3>
          <strong>{view.helpfulRate}</strong>
          <p>Respostas com nota 4 ou 5.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Hoje</h3>
          <strong>{view.recent24h}</strong>
          <p>Avaliações nas últimas 24h.</p>
        </article>
      </div>
    </div>
  );
}
