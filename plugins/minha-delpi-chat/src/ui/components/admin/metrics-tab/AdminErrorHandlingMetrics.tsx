import type { AdminErrorHandlingSummary } from "../../../../data/api/adminTypes";

type AdminErrorHandlingMetricsProps = {
  summary: AdminErrorHandlingSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export function AdminErrorHandlingMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminErrorHandlingMetricsProps) {
  const byType = summary?.byType ?? [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-error-handling-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 06</p>
          <h3 id="mdc-admin-error-handling-metrics-title">Erros e resultados vazios</h3>
          <p>
            Eventos classificados (`errorHandlingMetrics`) nas mensagens enviadas/stream na janela
            de {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de erro...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de erros.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Eventos</h4>
              <strong>{formatNumber(summary.totalEvents)}</strong>
              <p>Respostas com classificação de erro/vazio.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Recuperáveis</h4>
              <strong>{formatNumber(summary.recoverableCount)}</strong>
              <p>Com chips ou fluxo de recuperação.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Falha de API</h4>
              <strong>{formatNumber(summary.apiFailedCount)}</strong>
              <p>Sem afirmar inexistência de dados.</p>
            </article>
          </div>

          {byType.length ? (
            <div className="mdc-admin-drawing-metrics__table-wrap">
              <table className="mdc-admin-drawing-metrics__table">
                <thead>
                  <tr>
                    <th>Tipo</th>
                    <th>Ocorrências</th>
                  </tr>
                </thead>
                <tbody>
                  {byType.map((row) => (
                    <tr key={row.type}>
                      <td>{row.type}</td>
                      <td>{formatNumber(row.count)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="mdc-chat-muted">Nenhum evento de erro na janela selecionada.</p>
          )}
        </>
      ) : null}
    </section>
  );
}
