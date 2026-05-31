import type { AdminDocumentVisionSummary } from "../../../../data/api/adminTypes";

type AdminDocumentVisionMetricsProps = {
  summary: AdminDocumentVisionSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatPercent(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(value);
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

export function AdminDocumentVisionMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminDocumentVisionMetricsProps) {
  const engineEntries = summary
    ? Object.entries(summary.byEngine).sort((left, right) => right[1] - left[1])
    : [];

  return (
    <section
      className="mdc-admin-drawing-metrics mdc-admin-document-vision-metrics"
      aria-labelledby="mdc-admin-document-vision-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Onda 13</p>
          <h3 id="mdc-admin-document-vision-metrics-title">Visão de Documentos DELPI</h3>
          <p>
            Agregado de snapshots em auditoria (`metadata.documentVision`) na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de visão/OCR...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de visão de documentos.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Execuções OCR</h4>
              <strong>{formatNumber(summary.runsCount)}</strong>
              <p>Turnos com snapshot documentVision na janela.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Taxa legível</h4>
              <strong>{formatPercent(summary.legibilityRate)}</strong>
              <p>{formatNumber(summary.legibleCount)} execução(ões) marcadas como legíveis.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Duração média</h4>
              <strong>
                {summary.avgDurationMs != null ? `${formatNumber(summary.avgDurationMs)}ms` : "—"}
              </strong>
              <p>Tempo médio do pipeline de visão quando instrumentado.</p>
            </article>
          </div>

          {engineEntries.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Por motor</h4>
              <ul>
                {engineEntries.map(([engine, count]) => (
                  <li key={engine}>
                    <span>{engine}</span>
                    <strong>{formatNumber(count)}</strong>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {summary.recent.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__recent">
              <h4>Recentes</h4>
              <table>
                <thead>
                  <tr>
                    <th>Quando</th>
                    <th>Motor</th>
                    <th>Contexto</th>
                    <th>Legível</th>
                    <th>ms</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent.map((item, index) => (
                    <tr key={`${item.loggedAt ?? index}-${item.engine ?? "engine"}`}>
                      <td>{formatLoggedAt(item.loggedAt)}</td>
                      <td>{item.engine ?? "—"}</td>
                      <td>{item.context ?? "—"}</td>
                      <td>{item.legible === true ? "Sim" : item.legible === false ? "Não" : "—"}</td>
                      <td>{formatNumber(item.durationMs)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
