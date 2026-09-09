import type { AdminErrorHandlingSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { formatMetricNumber, formatMetricPercent } from "./adminMetricsFormatters";

import { ADMIN_HELP } from "../../../../content/adminHelpTooltips";

type AdminErrorHandlingMetricsProps = {
  summary: AdminErrorHandlingSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminErrorHandlingMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminErrorHandlingMetricsProps) {
  const byType = summary?.byType ?? [];

  return (
    <AdminMetricSection
      id="mdc-admin-error-handling-metrics-title"
      domain="Qualidade"
      title="Erros e resultados vazios"
      description={`Eventos classificados (errorHandlingMetrics) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de erro..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Eventos"
              value={formatMetricNumber(summary.totalEvents)}
              hint={ADMIN_HELP.kpis.errors.classified}
            />
            <AdminKpiCard
              title="Recuperáveis"
              value={formatMetricNumber(summary.recoverableCount)}
              hint={ADMIN_HELP.kpis.errors.recoveryUi}
            />
            <AdminKpiCard
              title="Falha de API"
              value={formatMetricNumber(summary.apiFailedCount)}
              hint={ADMIN_HELP.kpis.errors.noDenial}
            />
            <AdminKpiCard
              title="Planos auto-recuperação"
              value={formatMetricNumber(summary.autoRecoveryPlans)}
              hint={ADMIN_HELP.kpis.errors.retryPlan}
            />
            <AdminKpiCard
              title="Cliques recuperar"
              value={formatMetricNumber(summary.recoveryClicksCount)}
              hint={ADMIN_HELP.kpis.errors.recoverClicks}
            />
            <AdminKpiCard
              title="Tentativas automáticas"
              value={formatMetricNumber(summary.recoveryAttemptsCount)}
              hint={`${ADMIN_HELP.kpis.errors.recoverySuccess} ${formatMetricNumber(summary.recoverySuccessCount)} (${formatMetricPercent(summary.recoverySuccessRate)})`}
            />
          </AdminKpiGrid>

          {byType.length ? (
            <AdminDataTable
              title="Por tipo de evento"
              rows={byType}
              rowKey={(row) => row.type}
              columns={[
                { id: "type", header: "Tipo", render: (row) => row.type },
                {
                  id: "count",
                  header: "Ocorrências",
                  render: (row) => formatMetricNumber(row.count),
                },
              ]}
            />
          ) : (
            <p className="mdc-chat-muted">Nenhum evento de erro na janela selecionada.</p>
          )}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
