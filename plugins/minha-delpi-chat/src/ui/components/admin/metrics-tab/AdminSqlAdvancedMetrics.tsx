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
              hint="Conversas com skill SQL avançada ativa."
            />
            <AdminKpiCard
              title="Bloqueios"
              value={formatMetricNumber(summary.blockedCount)}
              hint="Comandos destrutivos detectados e recusados."
            />
            <AdminKpiCard
              title="Resultados vazios"
              value={formatMetricNumber(summary.emptyResultCount)}
              hint="Execuções sem linhas retornadas."
            />
            <AdminKpiCard
              title="Edição incremental"
              value={formatMetricNumber(summary.incrementalEditCount)}
              hint="Turnos com query ativa pronta para refinamento."
            />
            <AdminKpiCard
              title="CTEs / Window"
              value={`${formatMetricNumber(summary.cteUsageCount)} / ${formatMetricNumber(summary.windowFunctionUsageCount)}`}
              hint="Uso detectado em SQL gerado ou analisado."
            />
            <AdminKpiCard
              title="Prefetch schema"
              value={formatMetricNumber(summary.schemaPrefetchCount)}
              hint="Turnos que recomendaram explorar /system/tables/*."
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
