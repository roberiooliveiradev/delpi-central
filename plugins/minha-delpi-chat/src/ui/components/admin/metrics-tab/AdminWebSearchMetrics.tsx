import type { AdminWebSearchSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { formatMetricNumber, formatMetricPercent } from "./adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type AdminWebSearchMetricsProps = {
  summary: AdminWebSearchSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminWebSearchMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminWebSearchMetricsProps) {
  const alerts = summary?.alerts ?? [];

  return (
    <AdminMetricSection
      id="mdc-admin-web-search-metrics-title"
      domain="Qualidade"
      title="Pesquisa web confiável"
      description={`Agregado de webSearchMetrics e eventos de segurança/feedback na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de pesquisa web..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Pesquisas"
              value={formatMetricNumber(summary.totalSearches)}
              hint={ADMIN_HELP.kpis.webSearch.turns}
            />
            <AdminKpiCard
              title="Fonte oficial"
              value={formatMetricPercent(summary.officialSourceRate)}
              hint={`${formatMetricNumber(summary.withOfficialSourceCount)} ${ADMIN_HELP.kpis.webSearch.official}`}
            />
            <AdminKpiCard
              title="Baixa confiança"
              value={formatMetricNumber(summary.lowConfidenceCount)}
              hint={ADMIN_HELP.kpis.webSearch.lowConfidence}
            />
            <AdminKpiCard
              title="Sem resultado"
              value={formatMetricNumber(summary.noResultCount)}
              hint={ADMIN_HELP.kpis.webSearch.empty}
            />
            <AdminKpiCard
              title="Query sanitizada"
              value={formatMetricNumber(summary.redactedQueryCount)}
              hint={ADMIN_HELP.kpis.webSearch.redacted}
            />
            <AdminKpiCard
              title="Bloqueadas"
              value={formatMetricNumber(summary.blockedBySecurityCount)}
              hint={ADMIN_HELP.kpis.webSearch.skipped}
            />
            <AdminKpiCard
              title="Cliques pós-pesquisa"
              value={formatMetricNumber(summary.followUpClicksCount)}
              hint={ADMIN_HELP.kpis.webSearch.chips}
            />
            <AdminKpiCard
              title="Feedback negativo"
              value={formatMetricNumber(summary.negativeFeedbackCount)}
              hint={ADMIN_HELP.kpis.webSearch.reasons}
            />
          </AdminKpiGrid>

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

          {(summary.feedbackByReason?.length ?? 0) > 0 ? (
            <AdminDataTable
              title="Feedback por motivo"
              rows={summary.feedbackByReason}
              rowKey={(row) => row.reason}
              columns={[
                { id: "reason", header: "Motivo", render: (row) => row.reason },
                {
                  id: "count",
                  header: "Ocorrências",
                  render: (row) => formatMetricNumber(row.count),
                },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
