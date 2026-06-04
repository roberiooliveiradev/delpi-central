import type { AdminResponseEvaluationSummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard } from "../shared/AdminKpiCard";
import { AdminSummaryStrip } from "../shared/AdminSummaryStrip";
import { buildEvaluationsSummaryView } from "./evaluationsSummary";

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
      <AdminKpiCard title="Total" value={view.total} hint="Avaliações registradas." />
      <AdminKpiCard title="Média" value={view.averageScore} hint="Nota média (1–5)." />
      <AdminKpiCard title="Úteis" value={view.helpfulRate} hint="Respostas com nota 4 ou 5." />
      <AdminKpiCard title="Hoje" value={view.recent24h} hint="Avaliações nas últimas 24h." />
    </AdminSummaryStrip>
  );
}
