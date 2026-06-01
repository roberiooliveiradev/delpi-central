import type { AdminWebSearchSummary } from "../../../../data/api/adminTypes";

type AdminWebSearchMetricsProps = {
  summary: AdminWebSearchSummary | null;
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

  return `${Math.round(value * 100)}%`;
}

export function AdminWebSearchMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminWebSearchMetricsProps) {
  const alerts = summary?.alerts ?? [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-web-search-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 08</p>
          <h3 id="mdc-admin-web-search-metrics-title">Pesquisa web confiável</h3>
          <p>
            Agregado de `webSearchMetrics` e eventos de segurança/feedback na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de pesquisa web...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de pesquisa web.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Pesquisas</h4>
              <strong>{formatNumber(summary.totalSearches)}</strong>
              <p>Turnos com pesquisa web concluída ou tentada.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Fonte oficial</h4>
              <strong>{formatPercent(summary.officialSourceRate)}</strong>
              <p>{formatNumber(summary.withOfficialSourceCount)} com fonte oficial.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Baixa confiança</h4>
              <strong>{formatNumber(summary.lowConfidenceCount)}</strong>
              <p>Respostas com confiança classificada como baixa.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Sem resultado</h4>
              <strong>{formatNumber(summary.noResultCount)}</strong>
              <p>Busca vazia ou sem fonte confiável.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Query sanitizada</h4>
              <strong>{formatNumber(summary.redactedQueryCount)}</strong>
              <p>Dados sensíveis removidos antes da busca.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Bloqueadas</h4>
              <strong>{formatNumber(summary.blockedBySecurityCount)}</strong>
              <p>Consultas não enviadas ao buscador.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Cliques pós-pesquisa</h4>
              <strong>{formatNumber(summary.followUpClicksCount)}</strong>
              <p>Chips «Só fontes oficiais», «Buscar em inglês», etc.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Feedback negativo</h4>
              <strong>{formatNumber(summary.negativeFeedbackCount)}</strong>
              <p>Motivos específicos de pesquisa web.</p>
            </article>
          </div>

          {alerts.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Alertas</h4>
              <ul>
                {alerts.map((alert) => (
                  <li key={alert}>{alert}</li>
                ))}
              </ul>
            </div>
          ) : null}

          {(summary.feedbackByReason?.length ?? 0) > 0 ? (
            <div className="mdc-admin-drawing-metrics__table-wrap">
              <table className="mdc-admin-drawing-metrics__table">
                <thead>
                  <tr>
                    <th>Feedback (motivo)</th>
                    <th>Ocorrências</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.feedbackByReason.map((row) => (
                    <tr key={row.reason}>
                      <td>{row.reason}</td>
                      <td>{formatNumber(row.count)}</td>
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
