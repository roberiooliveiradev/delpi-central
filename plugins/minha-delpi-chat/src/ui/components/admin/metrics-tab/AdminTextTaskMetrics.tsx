import type { AdminTextTaskSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricLoggedAt,
  formatMetricNumber,
  rankedFromRecord,
} from "./adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type AdminTextTaskMetricsProps = {
  summary: AdminTextTaskSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminTextTaskMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminTextTaskMetricsProps) {
  const feedbackItems = summary?.feedback
    ? [
        { label: "Total avaliações", value: formatMetricNumber(summary.feedback.feedbackTotal), key: "total" },
        {
          label: "Negativos",
          value: formatMetricNumber(summary.feedback.feedbackNegative),
          key: "negative",
        },
        {
          label: "Positivos",
          value: formatMetricNumber(summary.feedback.feedbackPositive),
          key: "positive",
        },
        ...rankedFromRecord(summary.feedback.feedbackByReason),
      ]
    : [];

  return (
    <AdminMetricSection
      id="mdc-admin-text-task-metrics-title"
      domain="Qualidade"
      title="Especialista em textos"
      description={`Snapshots em auditoria (metadata.textTaskMetrics) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas textuais..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Tarefas textuais"
              value={formatMetricNumber(summary.textTasksCount)}
              hint={ADMIN_HELP.kpis.textTask.turns}
            />
            <AdminKpiCard
              title="Mistas"
              value={formatMetricNumber(summary.mixedTurnCount)}
              hint={ADMIN_HELP.kpis.textTask.mixed}
            />
            <AdminKpiCard
              title="Qualidade"
              value={formatMetricNumber(summary.qualityFailedCount)}
              hint={ADMIN_HELP.kpis.textTask.validatorFail}
            />
            <AdminKpiCard
              title="Lousa versionada"
              value={formatMetricNumber(summary.canvasVersionedCount)}
              hint={ADMIN_HELP.kpis.textTask.versions}
            />
            <AdminKpiCard
              title="Só versão final"
              value={formatMetricNumber(summary.deliverFinalOnlyCount)}
              hint={ADMIN_HELP.kpis.textTask.direct}
            />
            <AdminKpiCard
              title="Com anexo"
              value={formatMetricNumber(summary.attachmentSourceCount)}
              hint={ADMIN_HELP.kpis.textTask.fromFile}
            />
          </AdminKpiGrid>

          <div className="mdc-admin-metric-section__grid-3">
            <AdminRankedList title="Por subtipo" items={rankedFromRecord(summary.bySubtype)} />
            {feedbackItems.length > 0 ? (
              <AdminRankedList title="Feedback textual" items={feedbackItems} />
            ) : null}
            <AdminRankedList title="Por família" items={rankedFromRecord(summary.byFamily)} />
            <AdminRankedList title="Por intenção" items={rankedFromRecord(summary.byIntent)} />
          </div>

          {summary.recent.length > 0 ? (
            <AdminDataTable
              title="Recentes"
              rows={summary.recent}
              rowKey={(item, index) => `${item.loggedAt ?? "row"}-${index}`}
              columns={[
                { id: "when", header: "Quando", render: (item) => formatMetricLoggedAt(item.loggedAt) },
                { id: "subtype", header: "Subtipo", render: (item) => item.subtype ?? "—" },
                { id: "type", header: "Tipo", render: (item) => item.type ?? "—" },
                { id: "mixed", header: "Misto", render: (item) => (item.mixed ? "sim" : "—") },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
