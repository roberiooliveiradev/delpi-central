import type { AdminLearningSummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { formatMetricNumber, formatMetricPercent } from "../metrics-tab/adminMetricsFormatters";

type LearningSummaryStripProps = {
  summary: AdminLearningSummary | null;
  isLoading: boolean;
};

export function LearningSummaryStrip({ summary, isLoading }: LearningSummaryStripProps) {
  if (!summary) {
    return (
      <div className="mdc-admin-summary-strip" role="region" aria-label="Resumo de aprendizagem">
        <p className="mdc-chat-muted">{isLoading ? "Carregando métricas..." : "Sem métricas."}</p>
      </div>
    );
  }

  const cards: Array<{ key: string; title: string; value: string; hint?: string }> = [
    {
      key: "pending",
      title: "Pendentes",
      value: formatMetricNumber(summary.funnel.pending),
      hint: `${summary.highlights.pendingHighConfidence} alta confiança`,
    },
    {
      key: "created",
      title: "Criados (janela)",
      value: formatMetricNumber(summary.funnel.recentCreated),
      hint: `${summary.funnel.created} no total`,
    },
    {
      key: "promoted",
      title: "Promovidos",
      value: formatMetricNumber(summary.funnel.promoted),
      hint: `${summary.funnel.approved} aprovados`,
    },
    {
      key: "approval",
      title: "Taxa de aprovação",
      value: formatMetricPercent(summary.funnel.approvalRate),
      hint: `${summary.funnel.rejected} rejeitados`,
    },
    {
      key: "terms",
      title: "Termos ativos",
      value: formatMetricNumber(summary.highlights.learnedTermsActive),
      hint: `${summary.vocabulary.total} no vocabulário`,
    },
    {
      key: "defs",
      title: "Definições / Typos",
      value: `${formatMetricNumber(summary.highlights.termDefinitions)} / ${formatMetricNumber(summary.highlights.normalizationRules)}`,
      hint: "candidatos por tipo",
    },
    {
      key: "memory",
      title: "Memória ativa",
      value: formatMetricNumber(
        summary.highlights.memoryItemsActive ?? summary.memory?.active ?? 0,
      ),
      hint: `${summary.memory?.forgotten ?? 0} esquecidas`,
    },
    {
      key: "eval",
      title: "Testes falhando",
      value: formatMetricNumber(
        summary.highlights.evaluationCasesFailing ?? summary.evaluation?.failing ?? 0,
      ),
      hint: `${summary.highlights.evaluationCasesActive ?? summary.evaluation?.active ?? 0} casos ativos`,
    },
    {
      key: "ft",
      title: "Amostras (ajuste fino)",
      value: formatMetricNumber(
        summary.highlights.fineTuningSamplesApproved ?? summary.fineTuning?.samplesApproved ?? 0,
      ),
      hint: `${summary.fineTuning?.samplesCaptured ?? 0} capturadas`,
    },
    {
      key: "rag",
      title: "RAG indexado",
      value: formatMetricNumber(
        (summary.highlights.ragGlossaryIndexed ?? summary.ragIndex?.glossaryDocuments ?? 0) +
          (summary.highlights.ragUserMemoryIndexed ?? summary.ragIndex?.userMemoryDocuments ?? 0),
      ),
      hint: `glossário ${summary.ragIndex?.glossaryDocuments ?? 0} · memória ${summary.ragIndex?.userMemoryDocuments ?? 0}`,
    },
  ];

  const topTypos = summary.dashboard?.topTypoRules ?? [];

  return (
    <div className="mdc-admin-learning__kpis-wrap" role="region" aria-label="Resumo de aprendizagem">
      <AdminKpiGrid>
        {cards.map((card) => (
          <AdminKpiCard key={card.key} title={card.title} value={card.value} hint={card.hint} />
        ))}
      </AdminKpiGrid>
      {topTypos.length > 0 ? (
        <aside className="mdc-admin-learning__typo-hints">
          <span className="mdc-admin-learning__kpi-label">Erros de digitação frequentes</span>
          <ul>
            {topTypos.map((rule) => (
              <li key={`${rule.term}-${rule.normalizedTerm}`}>
                <code>{rule.term}</code> → <code>{rule.normalizedTerm}</code>
                {rule.evidenceCount > 0 ? ` (${rule.evidenceCount}×)` : ""}
              </li>
            ))}
          </ul>
        </aside>
      ) : null}
    </div>
  );
}
