import type { AdminPresentationSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricLoggedAt,
  formatMetricNumber,
  formatMetricPercent,
  rankedFromLabelCounts,
} from "./adminMetricsFormatters";

type AdminPresentationMetricsProps = {
  summary: AdminPresentationSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

type PresentationEventRow = {
  loggedAt?: string;
  event?: unknown;
  from?: unknown;
  to?: unknown;
  column?: unknown;
  filterKey?: unknown;
  filterValue?: unknown;
};

export function AdminPresentationMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminPresentationMetricsProps) {
  const alerts = summary?.alerts ?? [];
  const recentEvents = (summary?.recentEvents ?? []) as PresentationEventRow[];

  return (
    <AdminMetricSection
      id="mdc-admin-presentation-metrics-title"
      domain="Qualidade"
      title="Apresentação rica"
      description={`Impressões (presentationMetrics em mensagens) e interações (chat.presentation.event) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de apresentação..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          {alerts.length > 0 ? (
            <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
              <h3>Alertas</h3>
              <ul>
                {alerts.map((alert) => (
                  <li key={alert}>{alert}</li>
                ))}
              </ul>
            </article>
          ) : null}

          <AdminKpiGrid>
            <AdminKpiCard
              title="Respostas ricas"
              value={formatMetricNumber(summary.responsesWithRichPresentation)}
              hint="Turnos com gráfico/tabela/KPI e decisão registrada."
            />
            <AdminKpiCard
              title="Eventos de UI"
              value={formatMetricNumber(summary.eventsCount)}
              hint="Trocas de vista, eixo, tipo e exportações."
            />
            <AdminKpiCard
              title="Engajamento"
              value={formatMetricPercent(summary.engagementRate)}
              hint="Eventos por resposta rica (média na janela)."
            />
            <AdminKpiCard
              title="Troca de formato"
              value={formatMetricNumber(summary.viewSwitchCount)}
              hint={`${formatMetricPercent(summary.viewSwitchRate)} das respostas — texto ↔ tabela ↔ gráfico.`}
            />
            <AdminKpiCard
              title="→ Tabela"
              value={formatMetricNumber(summary.switchToTableCount)}
              hint={`${formatMetricPercent(summary.switchToTableRate)} das trocas de vista foram para tabela.`}
            />
            <AdminKpiCard
              title="Alteração de eixo"
              value={formatMetricNumber(summary.axisChangeCount)}
              hint={`${formatMetricPercent(summary.axisChangeRate)} das respostas ricas.`}
            />
            <AdminKpiCard
              title="Filtros categoria"
              value={formatMetricNumber(summary.categoryFilterCount)}
              hint="Filial, operador, centro, etc."
            />
            <AdminKpiCard
              title="Exportar PNG"
              value={formatMetricNumber(summary.exportPngCount)}
              hint="Downloads de gráfico."
            />
          </AdminKpiGrid>

          <div className="mdc-admin-metric-section__grid-3">
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Formatos escolhidos (API)"
                items={rankedFromLabelCounts(summary.topSelected)}
              />
            </article>
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Eventos mais frequentes"
                items={rankedFromLabelCounts(summary.topEvents)}
              />
            </article>
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Destino das trocas de vista"
                items={rankedFromLabelCounts(summary.topViewTargets)}
              />
            </article>
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Colunas de eixo alteradas"
                items={rankedFromLabelCounts(summary.topAxisColumns)}
              />
            </article>
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Filtros por categoria"
                items={rankedFromLabelCounts(summary.topFilterKeys)}
              />
            </article>
          </div>

          {recentEvents.length > 0 ? (
            <AdminDataTable
              title="Eventos recentes"
              rows={recentEvents}
              rowKey={(row, index) =>
                `${String(row.loggedAt ?? "row")}-${String(row.event ?? "event")}-${index}`
              }
              columns={[
                {
                  id: "loggedAt",
                  header: "Quando",
                  render: (row) => formatMetricLoggedAt(row.loggedAt),
                },
                {
                  id: "event",
                  header: "Evento",
                  render: (row) => String(row.event ?? "—"),
                },
                {
                  id: "transition",
                  header: "De → Para",
                  render: (row) => {
                    const from = row.from != null ? String(row.from) : "";
                    const to = row.to != null ? String(row.to) : "";
                    return from || to ? `${from || "—"} → ${to || "—"}` : "—";
                  },
                },
                {
                  id: "detail",
                  header: "Detalhe",
                  render: (row) =>
                    row.column != null
                      ? String(row.column)
                      : row.filterKey != null
                        ? `${row.filterKey}=${row.filterValue ?? ""}`
                        : "—",
                },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
