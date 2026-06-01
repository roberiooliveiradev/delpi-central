import type { AdminPresentationSummary } from "../../../../data/api/adminTypes";

type AdminPresentationMetricsProps = {
  summary: AdminPresentationSummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

export function AdminPresentationMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminPresentationMetricsProps) {
  const topSelected = summary?.topSelected ?? [];
  const topEvents = summary?.topEvents ?? [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-presentation-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 09</p>
          <h3 id="mdc-admin-presentation-metrics-title">Apresentação rica</h3>
          <p>
            Impressões (`presentationMetrics` em mensagens) e interações (`chat.presentation.event`)
            na janela de {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de apresentação...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de apresentação.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Respostas ricas</h4>
              <strong>{formatNumber(summary.responsesWithRichPresentation)}</strong>
              <p>Turnos com gráfico/tabela/KPI e decisão registrada.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Eventos de UI</h4>
              <strong>{formatNumber(summary.eventsCount)}</strong>
              <p>Trocas de vista, eixo, tipo e exportações.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Troca de formato</h4>
              <strong>{formatNumber(summary.viewSwitchCount)}</strong>
              <p>Texto ↔ tabela ↔ gráfico.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Filtros categoria</h4>
              <strong>{formatNumber(summary.categoryFilterCount)}</strong>
              <p>Filial, operador, centro, etc.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Export PNG</h4>
              <strong>{formatNumber(summary.exportPngCount)}</strong>
              <p>Downloads de gráfico.</p>
            </article>
          </div>

          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Formatos escolhidos</h4>
              {!topSelected.length ? (
                <p className="mdc-chat-muted">Sem dados na janela.</p>
              ) : (
                <ul className="mdc-admin-distribution-list">
                  {topSelected.map((item) => (
                    <li key={item.label}>
                      <span>{item.label}</span>
                      <strong>{formatNumber(item.count)}</strong>
                    </li>
                  ))}
                </ul>
              )}
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Eventos mais frequentes</h4>
              {!topEvents.length ? (
                <p className="mdc-chat-muted">Sem interações na janela.</p>
              ) : (
                <ul className="mdc-admin-distribution-list">
                  {topEvents.map((item) => (
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
