import type { AdminTypingCorrectionSummary } from "../../../../data/api/adminTypes";
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

type AdminTypingCorrectionMetricsProps = {
  summary: AdminTypingCorrectionSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

type TypingCorrectionEventRow = {
  loggedAt?: string;
  event?: unknown;
  original?: unknown;
  corrected?: unknown;
  changeCount?: unknown;
};

type TypingCorrectionAcceptanceRow = {
  loggedAt?: string;
  original?: unknown;
  corrected?: unknown;
  changeCount?: unknown;
  source?: unknown;
};

export function AdminTypingCorrectionMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminTypingCorrectionMetricsProps) {
  const alerts = summary?.alerts ?? [];
  const topCorrections = rankedFromLabelCounts(summary?.topCorrections ?? []);
  const recentEvents = (summary?.recentEvents ?? []) as TypingCorrectionEventRow[];
  const recentAcceptances = (summary?.recentAcceptances ??
    []) as TypingCorrectionAcceptanceRow[];

  return (
    <AdminMetricSection
      id="mdc-admin-typing-correction-metrics-title"
      domain="Qualidade"
      title="Corretor de digitação"
      description={`Sugestões no composer (chat.typing_correction.event) e aceites confirmados em turnos (typingCorrectionMetrics) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas do corretor de digitação..."
      isEmpty={!isLoading && !summary}
      emptyMessage="Não foi possível carregar o resumo do corretor de digitação."
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
              title="Sugestões oferecidas"
              value={formatMetricNumber(summary.offeredCount)}
              hint="Chips exibidos após debounce no composer."
            />
            <AdminKpiCard
              title="Aceites (evento)"
              value={formatMetricNumber(summary.acceptedCount)}
              hint="Cliques em «Enviar corrigido» registrados via help-events."
            />
            <AdminKpiCard
              title="Dispensadas"
              value={formatMetricNumber(summary.dismissedCount)}
              hint="Usuário manteve o texto original."
            />
            <AdminKpiCard
              title="Taxa de aceite"
              value={formatMetricPercent(summary.acceptanceRate)}
              hint="Aceites ÷ ofertas na janela."
            />
            <AdminKpiCard
              title="Turnos com aceite"
              value={formatMetricNumber(summary.acceptedTurnsCount)}
              hint="Mensagens enviadas com typingCorrection.accepted."
            />
            <AdminKpiCard
              title="Média de substituições"
              value={formatMetricNumber(summary.avgChangesPerAcceptance)}
              hint="Por turno aceito (auditoria)."
            />
          </AdminKpiGrid>

          {topCorrections.length > 0 ? (
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Correções mais frequentes"
                items={topCorrections}
                emptyMessage="Sem correções registradas."
              />
            </article>
          ) : null}

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
                  id: "original",
                  header: "Original",
                  render: (row) => String(row.original ?? "—"),
                },
                {
                  id: "corrected",
                  header: "Sugerido",
                  render: (row) => String(row.corrected ?? "—"),
                },
                {
                  id: "changeCount",
                  header: "Substituições",
                  render: (row) => String(row.changeCount ?? "—"),
                },
              ]}
            />
          ) : null}

          {recentAcceptances.length > 0 ? (
            <AdminDataTable
              title="Aceites recentes (turnos)"
              rows={recentAcceptances}
              rowKey={(row, index) =>
                `${String(row.loggedAt ?? "row")}-${String(row.original ?? "original")}-${index}`
              }
              columns={[
                {
                  id: "loggedAt",
                  header: "Quando",
                  render: (row) => formatMetricLoggedAt(row.loggedAt),
                },
                {
                  id: "original",
                  header: "Original",
                  render: (row) => String(row.original ?? "—"),
                },
                {
                  id: "corrected",
                  header: "Enviado",
                  render: (row) => String(row.corrected ?? "—"),
                },
                {
                  id: "changeCount",
                  header: "Substituições",
                  render: (row) => String(row.changeCount ?? "—"),
                },
                {
                  id: "source",
                  header: "Fonte",
                  render: (row) => String(row.source ?? "—"),
                },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
