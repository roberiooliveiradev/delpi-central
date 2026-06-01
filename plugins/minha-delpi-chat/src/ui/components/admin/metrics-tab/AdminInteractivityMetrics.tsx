import type { AdminInteractivitySummary } from "../../../../data/api/adminTypes";

type AdminInteractivityMetricsProps = {
  summary: AdminInteractivitySummary | null;
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

export function AdminInteractivityMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminInteractivityMetricsProps) {
  const topShown = summary?.topShown ?? [];
  const topClicked = summary?.topClicked ?? [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-interactivity-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 07</p>
          <h3 id="mdc-admin-interactivity-metrics-title">Interatividade (chips)</h3>
          <p>
            Impressões em auditoria (`interactivityMetrics`) e cliques (`chat.interactivity.clicked`)
            na janela de {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de interatividade...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de interatividade.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Respostas com chips</h4>
              <strong>{formatNumber(summary.responsesWithChips)}</strong>
              <p>Turnos com bloco consolidado de sugestões.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Chips exibidos</h4>
              <strong>{formatNumber(summary.suggestionsShownTotal)}</strong>
              <p>Total de sugestões mostradas (primários + overflow).</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Cliques</h4>
              <strong>{formatNumber(summary.clicksCount)}</strong>
              <p>Chips acionados pelo usuário.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>CTR geral</h4>
              <strong>{formatPercent(summary.clickThroughRate)}</strong>
              <p>Cliques ÷ impressões de chip.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>«Mais opções»</h4>
              <strong>{formatNumber(summary.moreOptionsResponses)}</strong>
              <p>Respostas que exibiram overflow agrupado.</p>
            </article>
          </div>

          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Mais exibidos</h4>
              {!topShown.length ? (
                <p className="mdc-chat-muted">Sem dados na janela.</p>
              ) : (
                <ul className="mdc-admin-distribution-list">
                  {topShown.map((item) => (
                    <li key={item.label}>
                      <span>{item.label}</span>
                      <strong>{formatNumber(item.count)}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Mais clicados</h4>
              {!topClicked.length ? (
                <p className="mdc-chat-muted">Sem cliques na janela.</p>
              ) : (
                <ul className="mdc-admin-distribution-list">
                  {topClicked.map((item) => (
                    <li key={item.label}>
                      <span>{item.label}</span>
                      <strong>{formatNumber(item.count)}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}
