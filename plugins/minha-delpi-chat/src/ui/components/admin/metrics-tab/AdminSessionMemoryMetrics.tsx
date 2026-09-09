import type { AdminSessionMemorySummary } from "../../../../data/api/adminTypes";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricLoggedAt,
  formatMetricNumber,
  formatMetricPercent,
  rankedFromRows,
} from "./adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type AdminSessionMemoryMetricsProps = {
  summary: AdminSessionMemorySummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminSessionMemoryMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminSessionMemoryMetricsProps) {
  const feedback = summary?.feedback;
  const recentItems =
    summary?.recent.map((item, index) => ({
      label: formatMetricLoggedAt(item.loggedAt),
      value: [
        item.assertivenessScore != null ? `score ${item.assertivenessScore}` : null,
        item.contextLossRisk ? "risco" : null,
        item.followUpDetected ? "follow-up" : null,
      ]
        .filter(Boolean)
        .join(" · ") || "—",
      key: `${item.loggedAt ?? index}`,
    })) ?? [];

  return (
    <AdminMetricSection
      id="mdc-admin-session-memory-metrics-title"
      domain="Qualidade"
      title="Contexto e assertividade"
      description={`sessionMemoryAdminMetrics e feedback de memória na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de memória..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Turnos com memória"
              value={formatMetricNumber(summary.memoryTurnsCount)}
              hint={ADMIN_HELP.kpis.memory.turns}
            />
            <AdminKpiCard
              title="Follow-ups"
              value={formatMetricNumber(summary.followUpTurns)}
              hint={`${ADMIN_HELP.kpis.memory.resolution} ${formatMetricPercent(summary.followUpResolutionRate)}.`}
            />
            <AdminKpiCard
              title="Risco de perda"
              value={formatMetricNumber(summary.contextLossRiskTurns)}
              hint={ADMIN_HELP.kpis.memory.lowAssert}
            />
            <AdminKpiCard
              title="Assertividade < 70"
              value={formatMetricNumber(summary.lowAssertivenessTurns)}
              hint={ADMIN_HELP.kpis.memory.lowScore}
            />
            <AdminKpiCard
              title="Ambiguidade"
              value={formatMetricNumber(summary.ambiguityTurns)}
              hint={ADMIN_HELP.kpis.memory.unresolved}
            />
            <AdminKpiCard
              title="Feedback memória"
              value={formatMetricNumber(feedback?.memoryFeedbackCount)}
              hint={`${ADMIN_HELP.kpis.memory.lostContext} ${formatMetricNumber(feedback?.lostContextFeedbackCount)}.`}
            />
          </AdminKpiGrid>

          {(summary.alerts?.length ?? 0) > 0 ? (
            <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
              <h3>Alertas</h3>
              <ul>
                {summary.alerts.map((alert) => (
                  <li key={alert.code}>
                    <strong>{alert.code}</strong> — {alert.message}
                  </li>
                ))}
              </ul>
            </article>
          ) : null}

          <div className="mdc-admin-metric-section__grid-2">
            <AdminRankedList
              title="Flags de assertividade"
              items={rankedFromRows(summary.assertivenessFlags)}
            />
            <AdminRankedList title="Turnos recentes" items={recentItems} />
          </div>
        </>
      ) : null}
    </AdminMetricSection>
  );
}
