import type { AdminFeedbackSummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricNumber,
  formatMetricPercent,
  rankedFromRows,
} from "./adminMetricsFormatters";

type AdminFeedbackMetricsProps = {
  summary: AdminFeedbackSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminFeedbackMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminFeedbackMetricsProps) {
  return (
    <AdminMetricSection
      id="mdc-admin-feedback-metrics-title"
      domain="Qualidade"
      title="Feedback do usuário"
      description={`Thumbs up/down com contexto técnico (ai_chat_message_feedback) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de feedback..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard title="CSAT" value={formatMetricPercent(summary.csat)} hint="Feedback positivo ÷ total." />
            <AdminKpiCard title="Positivos" value={formatMetricNumber(summary.positiveCount)} />
            <AdminKpiCard title="Negativos" value={formatMetricNumber(summary.negativeCount)} />
            <AdminKpiCard title="Perda de contexto" value={formatMetricNumber(summary.lostContextCount)} />
          </AdminKpiGrid>

          {summary.alerts?.length ? (
            <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
              <h3>Alertas de qualidade</h3>
              <ul>
                {summary.alerts.map((alert) => (
                  <li key={alert.code}>{alert.message}</li>
                ))}
              </ul>
            </article>
          ) : null}

          <div className="mdc-admin-metric-section__grid-3">
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Top motivos negativos"
                items={rankedFromRows(summary.feedbackByReason, 8)}
              />
            </article>
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Por intenção"
                items={rankedFromRows(summary.feedbackByIntent, 8)}
              />
            </article>
            <article className="mdc-admin-kpi-card">
              <AdminRankedList
                title="Por agente"
                items={rankedFromRows(summary.feedbackByAgent, 8)}
              />
            </article>
          </div>
        </>
      ) : null}
    </AdminMetricSection>
  );
}
