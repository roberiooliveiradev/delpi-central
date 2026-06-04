import type { ToolsSummary } from "./toolsSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

type ToolsSummaryStripProps = {
  summary: ToolsSummary;
};

export function ToolsSummaryStrip({ summary }: ToolsSummaryStripProps) {
  return (
    <AdminSummaryStrip ariaLabel="Resumo de ferramentas e integrações">
      <AdminKpiCard
        title="LLM"
        value={summary.llmConfigured ? "Configurado" : "—"}
        hint={summary.llmLabel}
      />
      <AdminKpiCard title="Saúde" value={summary.healthLabel} hint="Checks operacionais do catálogo." />
      <AdminKpiCard
        title="Actions globais"
        value={formatMetricNumber(summary.globalActions)}
        hint="Rotas OpenAPI administradas."
      />
      <AdminKpiCard
        title="Actions no chat"
        value={formatMetricNumber(summary.chatActions)}
        hint="Itens expostos ao catálogo do usuário."
      />
    </AdminSummaryStrip>
  );
}
