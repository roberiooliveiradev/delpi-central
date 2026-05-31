import type { AdminIntentRoutingSummary } from "../../../../data/api/adminTypes";

type AdminIntentRoutingMetricsProps = {
  summary: AdminIntentRoutingSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
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

export function AdminIntentRoutingMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminIntentRoutingMetricsProps) {
  const intentEntries = summary
    ? Object.entries(summary.byIntent).sort((left, right) => right[1] - left[1])
    : [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-intent-routing-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 02</p>
          <h3 id="mdc-admin-intent-routing-metrics-title">Roteamento de intenção</h3>
          <p>
            Agregado de snapshots em auditoria (`metadata.intentRouting`) na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de roteamento...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de roteamento.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Rotas</h4>
              <strong>{formatNumber(summary.routesCount)}</strong>
              <p>Turnos com snapshot de intentRouting na janela.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Ambíguos</h4>
              <strong>{formatNumber(summary.ambiguousCount)}</strong>
              <p>Pedidos com escopo operacional incerto (desambiguação).</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Mixed tasks</h4>
              <strong>{formatNumber(summary.mixedTaskCount)}</strong>
              <p>Pedidos compostos (operacional + texto/web/etc.).</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Web</h4>
              <strong>{formatNumber(summary.webSearchCount)}</strong>
              <p>Rotas com pesquisa web explícita.</p>
            </article>
          </div>

          {intentEntries.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Por intenção</h4>
              <ul>
                {intentEntries.map(([intent, count]) => (
                  <li key={intent}>
                    <span>{intent}</span>
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
                    <th>Intent</th>
                    <th>Sub</th>
                    <th>Decisão</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent.map((item, index) => (
                    <tr key={`${item.loggedAt}-${index}`}>
                      <td>{formatLoggedAt(item.loggedAt)}</td>
                      <td>{item.intent ?? "—"}</td>
                      <td>{item.subIntent ?? "—"}</td>
                      <td>{item.decision ?? "—"}</td>
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
