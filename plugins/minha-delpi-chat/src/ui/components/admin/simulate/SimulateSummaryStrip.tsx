import type { SimulateSummary } from "./simulateSummary";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { formatMetricNumber } from "../metrics-tab/adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type SimulateSummaryStripProps = {
  summary: SimulateSummary;
};

export function SimulateSummaryStrip({ summary }: SimulateSummaryStripProps) {
  return (
    <AdminSummaryStrip ariaLabel="Resumo da simulação">
      <AdminKpiCard
        title="Agentes"
        value={formatMetricNumber(summary.agentCount)}
        hint={ADMIN_HELP.kpis.simulate.agents}
      />
      <AdminKpiCard
        title="Sessões"
        value={formatMetricNumber(summary.sessionCount)}
        hint={ADMIN_HELP.kpis.simulate.sessions}
      />
      <AdminKpiCard
        title="Resultado"
        value={summary.hasResult ? "Pronto" : "—"}
        hint={ADMIN_HELP.kpis.simulate.result}
        active={summary.hasResult}
      />
    </AdminSummaryStrip>
  );
}
