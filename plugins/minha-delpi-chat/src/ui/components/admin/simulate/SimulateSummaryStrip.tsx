import type { SimulateSummary } from "./simulateSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

type SimulateSummaryStripProps = {
  summary: SimulateSummary;
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function SimulateSummaryStrip({ summary }: SimulateSummaryStripProps) {
  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo da simulação"
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>Agentes</h3>
          <strong>{formatCount(summary.agentCount)}</strong>
          <p>Disponíveis para sandbox.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Sessões</h3>
          <strong>{formatCount(summary.sessionCount)}</strong>
          <p>Histórico opcional na simulação.</p>
        </article>
        <article
          className={["mdc-admin-kpi-card", summary.hasResult ? "is-active" : ""]
            .filter(Boolean)
            .join(" ")}
        >
          <h3>Resultado</h3>
          <strong>{summary.hasResult ? "Pronto" : "—"}</strong>
          <p>Prompt, RAG e tools após simular.</p>
        </article>
      </div>
    </div>
  );
}
