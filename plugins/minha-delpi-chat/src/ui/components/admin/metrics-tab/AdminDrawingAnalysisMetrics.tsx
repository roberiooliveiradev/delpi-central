import type { AdminDrawingAnalysisSummary } from "../../../../data/api/adminTypes";

type AdminDrawingAnalysisMetricsProps = {
  summary: AdminDrawingAnalysisSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    approved: "Aprovado",
    rejected: "Reprovado",
    warning: "Alerta",
    unknown: "Indefinido",
  };

  return labels[status] ?? status;
}

function formatLoggedAt(value?: string | null): string {
  if (!value) {
    return "—";
  }

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("pt-BR");
}

export function AdminDrawingAnalysisMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminDrawingAnalysisMetricsProps) {
  const statusEntries = summary
    ? Object.entries(summary.byStatus).sort((left, right) => right[1] - left[1])
    : [];

  return (
    <section className="mdc-admin-drawing-metrics" aria-labelledby="mdc-admin-drawing-metrics-title">
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Onda 12</p>
          <h3 id="mdc-admin-drawing-metrics-title">Análise de Desenhos DELPI</h3>
          <p>
            Agregado de snapshots em auditoria (`metadata.drawingAnalysis`) na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de desenho...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de análises de desenho.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Análises</h4>
              <strong>{formatNumber(summary.analysesCount)}</strong>
              <p>Turnos com snapshot de drawingAnalysis na janela.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Produtos distintos</h4>
              <strong>{formatNumber(summary.uniqueProductCodes)}</strong>
              <p>Códigos únicos detectados nos snapshots.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Erros críticos</h4>
              <strong>{formatNumber(summary.totalCriticalErrors)}</strong>
              <p>Soma de `criticalErrors` nos snapshots.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Relatório exportado</h4>
              <strong>{formatNumber(summary.reportExportedCount)}</strong>
              <p>Turnos com flag `reportExported`.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Analyser OK</h4>
              <strong>{formatNumber(summary.analyserOkCount)}</strong>
              <p>Chamadas ao analyser concluídas com sucesso.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Com PDF</h4>
              <strong>{formatNumber(summary.withPdfCount)}</strong>
              <p>Turnos com anexo PDF na conversa.</p>
            </article>
          </div>

          <div className="mdc-admin-metrics-tab__columns">
            <article className="mdc-admin-kpi-card">
              <h4>Por status</h4>
              {statusEntries.length === 0 ? (
                <p>Nenhuma análise registrada na janela.</p>
              ) : (
                <ul className="mdc-admin-distribution-list">
                  {statusEntries.map(([status, count]) => (
                    <li key={status}>
                      <span>{formatStatusLabel(status)}</span>
                      <strong>{formatNumber(count)}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
              <h4>Últimas análises</h4>
              {summary.recent.length === 0 ? (
                <p>Sem eventos recentes com snapshot.</p>
              ) : (
                <div className="mdc-admin-metrics-tab__table-wrap">
                  <table className="mdc-admin-metrics-tab__table">
                    <thead>
                      <tr>
                        <th>Quando</th>
                        <th>Produto</th>
                        <th>Status</th>
                        <th>Críticos</th>
                        <th>Exportado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {summary.recent.map((item, index) => (
                        <tr key={`${item.loggedAt ?? "row"}-${index}`}>
                          <td>{formatLoggedAt(item.loggedAt)}</td>
                          <td>{item.productCode ?? "—"}</td>
                          <td>{formatStatusLabel(String(item.overallStatus ?? "unknown"))}</td>
                          <td>{formatNumber(item.criticalErrors)}</td>
                          <td>{item.reportExported ? "Sim" : "Não"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}
