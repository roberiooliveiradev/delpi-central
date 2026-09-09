import type { AdminIntentRoutingSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricLoggedAt,
  formatMetricNumber,
} from "./adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type AdminIntentRoutingMetricsProps = {
  summary: AdminIntentRoutingSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminIntentRoutingMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminIntentRoutingMetricsProps) {
  const intentEntries = summary
    ? Object.entries(summary.byIntent)
        .sort((left, right) => right[1] - left[1])
        .map(([intent, count]) => ({
          label: intent,
          value: formatMetricNumber(count),
          key: intent,
        }))
    : [];

  return (
    <AdminMetricSection
      id="mdc-admin-intent-routing-metrics-title"
      domain="Qualidade"
      title="Roteamento de intenção"
      description={`Agregado de snapshots em auditoria (metadata.intentRouting) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de roteamento..."
      isEmpty={!isLoading && !summary}
      emptyMessage="Não foi possível carregar o resumo de roteamento."
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Rotas"
              value={formatMetricNumber(summary.routesCount)}
              hint={ADMIN_HELP.kpis.intent.turns}
            />
            <AdminKpiCard
              title="Ambíguos"
              value={formatMetricNumber(summary.ambiguousCount)}
              hint={ADMIN_HELP.kpis.intent.ambiguous}
            />
            <AdminKpiCard
              title="Tarefas mistas"
              value={formatMetricNumber(summary.mixedTaskCount)}
              hint={ADMIN_HELP.kpis.intent.compound}
            />
            <AdminKpiCard
              title="Web"
              value={formatMetricNumber(summary.webSearchCount)}
              hint={ADMIN_HELP.kpis.intent.web}
            />
          </AdminKpiGrid>

          {intentEntries.length > 0 ? (
            <AdminRankedList title="Por intenção" items={intentEntries} />
          ) : null}

          {summary.recent.length > 0 ? (
            <AdminDataTable
              title="Recentes"
              caption="Últimos roteamentos de intenção registrados na janela"
              rows={summary.recent}
              rowKey={(item, index) => `${item.loggedAt ?? "row"}-${index}`}
              columns={[
                {
                  id: "when",
                  header: "Quando",
                  render: (item) => formatMetricLoggedAt(item.loggedAt),
                },
                {
                  id: "intent",
                  header: "Intent",
                  render: (item) => item.intent ?? "—",
                },
                {
                  id: "sub",
                  header: "Sub",
                  render: (item) => item.subIntent ?? "—",
                },
                {
                  id: "decision",
                  header: "Decisão",
                  render: (item) => item.decision ?? "—",
                },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
