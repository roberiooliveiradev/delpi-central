import type { SimulateSummary } from "./simulateSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

type SimulateSummaryStripProps = {
  summary: SimulateSummary;
};

export function SimulateSummaryStrip({ summary }: SimulateSummaryStripProps) {
  return (
    <AdminSummaryStrip ariaLabel="Resumo da simulação">
      <AdminKpiCard
        title="Agentes"
        value={formatMetricNumber(summary.agentCount)}
        hint="Disponíveis para sandbox."
      />
      <AdminKpiCard
        title="Sessões"
        value={formatMetricNumber(summary.sessionCount)}
        hint="Histórico opcional na simulação."
      />
      <AdminKpiCard
        title="Resultado"
        value={summary.hasResult ? "Pronto" : "—"}
        hint="Prompt, RAG e ferramentas após simular."
        active={summary.hasResult}
      />
    </AdminSummaryStrip>
  );
}
