import type { ToolsSummary } from "./toolsSummary";

import "../knowledge/KnowledgeSummaryStrip.css";

type ToolsSummaryStripProps = {
  summary: ToolsSummary;
};

function formatCount(value: number): string {
  return new Intl.NumberFormat("pt-BR").format(value);
}

export function ToolsSummaryStrip({ summary }: ToolsSummaryStripProps) {
  return (
    <div
      className="mdc-admin-knowledge-summary"
      role="region"
      aria-label="Resumo de ferramentas e integrações"
    >
      <div className="mdc-admin-knowledge-summary__grid mdc-admin-kpi-grid">
        <article className="mdc-admin-kpi-card">
          <h3>LLM</h3>
          <strong>{summary.llmConfigured ? "Configurado" : "—"}</strong>
          <p>{summary.llmLabel}</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Saúde</h3>
          <strong>{summary.healthLabel}</strong>
          <p>Checks operacionais do catálogo.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Actions globais</h3>
          <strong>{formatCount(summary.globalActions)}</strong>
          <p>Rotas OpenAPI administradas.</p>
        </article>
        <article className="mdc-admin-kpi-card">
          <h3>Actions no chat</h3>
          <strong>{formatCount(summary.chatActions)}</strong>
          <p>Itens expostos ao catálogo do usuário.</p>
        </article>
      </div>
    </div>
  );
}
