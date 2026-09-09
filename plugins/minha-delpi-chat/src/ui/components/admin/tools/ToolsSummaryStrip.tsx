import type { ToolsSummary } from "./toolsSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

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
      <AdminKpiCard
        title="Saúde"
        value={summary.healthLabel}
        hint={ADMIN_HELP.kpis.tools.health}
      />
      <AdminKpiCard
        title="Ações globais"
        value={formatMetricNumber(summary.globalActions)}
        hint={ADMIN_HELP.kpis.tools.routes}
      />
      <AdminKpiCard
        title="Ações no chat"
        value={formatMetricNumber(summary.chatActions)}
        hint={ADMIN_HELP.kpis.tools.exposed}
      />
    </AdminSummaryStrip>
  );
}
