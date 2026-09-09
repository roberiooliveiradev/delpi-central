import type { AdminSqlAdvancedSummary } from "../../../../data/api/adminTypes";
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

type AdminSqlAdvancedMetricsProps = {
  summary: AdminSqlAdvancedSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatModeLabel(mode?: string | null): string {
  const labels: Record<string, string> = {
    create: "Criação",
    review: "Revisão",
    explain: "Explicação",
    optimize: "Otimização",
    execute: "Execução",
    schema_explore: "Schema",
    incremental_edit: "Edição incremental",
    analyze_result: "Análise de resultado",
    visualize: "Visualização",
  };

  if (!mode) {
    return "—";
  }

  return labels[mode] ?? mode;
}

export function AdminSqlAdvancedMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminSqlAdvancedMetricsProps) {
  const modeItems = rankedFromRecord(summary?.byMode).map((item) => ({
    ...item,
    label: formatModeLabel(item.label),
  }));

  return (
    <AdminMetricSection
      id="mdc-admin-sql-advanced-metrics-title"
      domain="Qualidade"
      title="SQL avançado"
      description={`Snapshots em auditoria (metadata.sqlAdvancedMetrics) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas SQL..."
      isEmpty={!isLoading && !summary}
      className="mdc-admin-sql-advanced-metrics"
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Turnos SQL"
              value={formatMetricNumber(summary.runsCount)}
              hint={ADMIN_HELP.kpis.sql.skillOn}
            />
            <AdminKpiCard
              title="Bloqueios"
              value={formatMetricNumber(summary.blockedCount)}
              hint={ADMIN_HELP.kpis.sql.destructive}
            />
            <AdminKpiCard
              title="Resultados vazios"
              value={formatMetricNumber(summary.emptyResultCount)}
              hint={ADMIN_HELP.kpis.sql.empty}
            />
            <AdminKpiCard
              title="Edição incremental"
              value={formatMetricNumber(summary.incrementalEditCount)}
              hint={ADMIN_HELP.kpis.sql.ready}
            />
            <AdminKpiCard
              title="CTEs / Window"
              value={`${formatMetricNumber(summary.cteUsageCount)} / ${formatMetricNumber(summary.windowFunctionUsageCount)}`}
              hint={ADMIN_HELP.kpis.sql.usage}
            />
            <AdminKpiCard
              title="Prefetch schema"
              value={formatMetricNumber(summary.schemaPrefetchCount)}
              hint={ADMIN_HELP.kpis.sql.catalogHint}
            />
          </AdminKpiGrid>

          <div className="mdc-admin-metric-section__grid-3">
            <AdminRankedList title="Por modo" items={modeItems} />
            <AdminRankedList title="Por dialeto" items={rankedFromRecord(summary.byDialect)} />
            <AdminRankedList title="Visualização sugerida" items={rankedFromRecord(summary.byChartType)} />
          </div>

          {summary.recent.length > 0 ? (
            <AdminDataTable
              title="Recentes"
              rows={summary.recent}
              rowKey={(item, index) => `${item.loggedAt ?? index}-${item.mode ?? "mode"}`}
              columns={[
                { id: "when", header: "Quando", render: (item) => formatMetricLoggedAt(item.loggedAt) },
                { id: "mode", header: "Modo", render: (item) => formatModeLabel(item.mode) },
                { id: "dialect", header: "Dialeto", render: (item) => item.dialect ?? "—" },
                { id: "blocked", header: "Bloqueado", render: (item) => (item.blocked ? "Sim" : "Não") },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
