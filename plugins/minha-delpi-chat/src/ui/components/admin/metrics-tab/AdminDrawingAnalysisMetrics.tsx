import type { AdminDrawingAnalysisSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricLoggedAt,
  formatMetricNumber,
  rankedFromRecord,
} from "./adminMetricsFormatters";

type AdminDrawingAnalysisMetricsProps = {
  summary: AdminDrawingAnalysisSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

const STATUS_LABELS: Record<string, string> = {
  approved: "Aprovado",
  rejected: "Reprovado",
  warning: "Alerta",
  unknown: "Indefinido",
};

function formatStatusLabel(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export function AdminDrawingAnalysisMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminDrawingAnalysisMetricsProps) {
  const statusItems = rankedFromRecord(summary?.byStatus).map((item) => ({
    ...item,
    label: formatStatusLabel(item.label),
  }));

  return (
    <AdminMetricSection
      id="mdc-admin-drawing-metrics-title"
      domain="Qualidade"
      title="Análise de Desenhos DELPI"
      description={`Agregado de snapshots em auditoria (metadata.drawingAnalysis) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de desenho..."
      isEmpty={!isLoading && !summary}
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Análises"
              value={formatMetricNumber(summary.analysesCount)}
              hint="Turnos com snapshot de drawingAnalysis na janela."
            />
            <AdminKpiCard
              title="Produtos distintos"
              value={formatMetricNumber(summary.uniqueProductCodes)}
              hint="Códigos únicos detectados nos snapshots."
            />
            <AdminKpiCard
              title="Erros críticos"
              value={formatMetricNumber(summary.totalCriticalErrors)}
              hint="Soma de criticalErrors nos snapshots."
            />
            <AdminKpiCard
              title="Relatório exportado"
              value={formatMetricNumber(summary.reportExportedCount)}
              hint="Turnos com flag reportExported."
            />
            <AdminKpiCard
              title="Analyser OK"
              value={formatMetricNumber(summary.analyserOkCount)}
              hint="Chamadas ao analyser concluídas com sucesso."
            />
            <AdminKpiCard
              title="Com PDF"
              value={formatMetricNumber(summary.withPdfCount)}
              hint="Turnos com anexo PDF na conversa."
            />
          </AdminKpiGrid>

          <div className="mdc-admin-metric-section__grid-2">
            <article className="mdc-admin-kpi-card">
              <AdminRankedList title="Por status" items={statusItems} />
            </article>
            <AdminDataTable
              title="Últimas análises"
              rows={summary.recent}
              rowKey={(row, index) => `${row.loggedAt ?? "row"}-${index}`}
              columns={[
                {
                  id: "loggedAt",
                  header: "Quando",
                  render: (row) => formatMetricLoggedAt(row.loggedAt),
                },
                {
                  id: "product",
                  header: "Produto",
                  render: (row) => row.productCode ?? "—",
                },
                {
                  id: "status",
                  header: "Status",
                  render: (row) => formatStatusLabel(String(row.overallStatus ?? "unknown")),
                },
                {
                  id: "critical",
                  header: "Críticos",
                  render: (row) => formatMetricNumber(row.criticalErrors),
                },
                {
                  id: "exported",
                  header: "Exportado",
                  render: (row) => (row.reportExported ? "Sim" : "Não"),
                },
              ]}
            />
          </div>
        </>
      ) : null}
    </AdminMetricSection>
  );
}
