import type { AdminResponseEvaluationSummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { buildEvaluationsSummaryView } from "./evaluationsSummary";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

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
    <AdminSummaryStrip ariaLabel="Resumo de avaliações de respostas" isLoading={isLoading}>
      <AdminKpiCard title="Total" value={view.total} hint={ADMIN_HELP.kpis.evaluations.total} />
      <AdminKpiCard title="Média" value={view.averageScore} hint={ADMIN_HELP.kpis.evaluations.average} />
      <AdminKpiCard title="Úteis" value={view.helpfulRate} hint={ADMIN_HELP.kpis.evaluations.helpful} />
      <AdminKpiCard title="Hoje" value={view.recent24h} hint={ADMIN_HELP.kpis.evaluations.recent} />
    </AdminSummaryStrip>
  );
}
