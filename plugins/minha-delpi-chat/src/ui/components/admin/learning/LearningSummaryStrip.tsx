import type { AdminLearningSummary } from "../../../../data/api/adminTypes";

type LearningSummaryStripProps = {
  summary: AdminLearningSummary | null;
  isLoading: boolean;
};

function formatPercent(value: number | null): string {
  if (value === null || Number.isNaN(value)) {
    return "—";
  }
  return `${Math.round(value * 100)}%`;
}

export function LearningSummaryStrip({ summary, isLoading }: LearningSummaryStripProps) {
  if (!summary) {
    return (
      <div className="mdc-admin-learning__kpis">
        <p className="mdc-chat-muted">{isLoading ? "Carregando métricas..." : "Sem métricas."}</p>
      </div>
    );
  }

  const cards: Array<{ label: string; value: string; hint?: string }> = [
    {
      label: "Pendentes",
      value: String(summary.funnel.pending),
      hint: `${summary.highlights.pendingHighConfidence} alta confiança`,
    },
    {
      label: "Criados (janela)",
      value: String(summary.funnel.recentCreated),
      hint: `${summary.funnel.created} no total`,
    },
    {
      label: "Promovidos",
      value: String(summary.funnel.promoted),
      hint: `${summary.funnel.approved} aprovados`,
    },
    {
      label: "Taxa de aprovação",
      value: formatPercent(summary.funnel.approvalRate),
      hint: `${summary.funnel.rejected} rejeitados`,
    },
    {
      label: "Termos ativos",
      value: String(summary.highlights.learnedTermsActive),
      hint: `${summary.vocabulary.total} no vocabulário`,
    },
    {
      label: "Definições / Typos",
      value: `${summary.highlights.termDefinitions} / ${summary.highlights.normalizationRules}`,
      hint: "candidatos por tipo",
    },
    {
      label: "Memória ativa",
      value: String(summary.highlights.memoryItemsActive ?? summary.memory?.active ?? 0),
      hint: `${summary.memory?.forgotten ?? 0} esquecidas`,
    },
  ];

  return (
    <div className="mdc-admin-learning__kpis">
      {cards.map((card) => (
        <article key={card.label} className="mdc-admin-learning__kpi">
          <span className="mdc-admin-learning__kpi-label">{card.label}</span>
          <strong className="mdc-admin-learning__kpi-value">{card.value}</strong>
          {card.hint ? (
            <small className="mdc-admin-learning__kpi-hint">{card.hint}</small>
          ) : null}
        </article>
      ))}
    </div>
  );
}
