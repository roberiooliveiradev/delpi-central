import type { AdminDocumentVisionSummary } from "../../../../data/api/adminTypes";
import { AdminDataTable } from "../shared/AdminDataTable";
import { AdminKpiCard, AdminKpiGrid } from "../shared/AdminKpiCard";
import { AdminMetricSection } from "../shared/AdminMetricSection";
import { AdminRankedList } from "../shared/AdminRankedList";
import {
  formatMetricLoggedAt,
  formatMetricNumber,
  formatMetricPercent,
  rankedFromRecord,
} from "./adminMetricsFormatters";

type AdminDocumentVisionMetricsProps = {
  summary: AdminDocumentVisionSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

export function AdminDocumentVisionMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminDocumentVisionMetricsProps) {
  return (
    <AdminMetricSection
      id="mdc-admin-document-vision-metrics-title"
      domain="Qualidade"
      title="Visão de documentos"
      description={`Snapshots em auditoria (metadata.documentVision) na janela de ${
        summary?.windowHours ?? windowHours
      }h.`}
      isLoading={isLoading}
      loadingMessage="Carregando métricas de visão/OCR..."
      isEmpty={!isLoading && !summary}
      className="mdc-admin-document-vision-metrics"
    >
      {summary ? (
        <>
          <AdminKpiGrid>
            <AdminKpiCard
              title="Execuções OCR"
              value={formatMetricNumber(summary.runsCount)}
              hint="Turnos com snapshot documentVision na janela."
            />
            <AdminKpiCard
              title="Taxa legível"
              value={formatMetricPercent(summary.legibilityRate)}
              hint={`${formatMetricNumber(summary.legibleCount)} execução(ões) legíveis.`}
            />
            <AdminKpiCard
              title="Duração média"
              value={
                summary.avgDurationMs != null
                  ? `${formatMetricNumber(summary.avgDurationMs)} ms`
                  : "—"
              }
              hint="Tempo médio do pipeline de visão quando instrumentado."
            />
          </AdminKpiGrid>

          <div className="mdc-admin-metric-section__grid-2">
            <AdminRankedList title="Por motor" items={rankedFromRecord(summary.byEngine)} />
            <AdminRankedList title="Por estágio" items={rankedFromRecord(summary.byStage)} />
          </div>

          {summary.recent.length > 0 ? (
            <AdminDataTable
              title="Recentes"
              rows={summary.recent}
              rowKey={(item, index) => `${item.loggedAt ?? index}-${item.engine ?? "engine"}`}
              columns={[
                { id: "when", header: "Quando", render: (item) => formatMetricLoggedAt(item.loggedAt) },
                { id: "engine", header: "Motor", render: (item) => item.engine ?? "—" },
                { id: "context", header: "Contexto", render: (item) => item.context ?? "—" },
                {
                  id: "legible",
                  header: "Legível",
                  render: (item) =>
                    item.legible === true ? "Sim" : item.legible === false ? "Não" : "—",
                },
                {
                  id: "ms",
                  header: "ms",
                  render: (item) => formatMetricNumber(item.durationMs),
                },
              ]}
            />
          ) : null}
        </>
      ) : null}
    </AdminMetricSection>
  );
}
