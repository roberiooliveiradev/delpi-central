import type { AdminFeedbackSummary } from "../../../../data/api/adminTypes";

type AdminFeedbackMetricsProps = {
  summary: AdminFeedbackSummary | null;
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

export function AdminFeedbackMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminFeedbackMetricsProps) {
  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-feedback-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 10</p>
          <h3 id="mdc-admin-feedback-metrics-title">Feedback do usuário</h3>
          <p>
            Thumbs up/down com contexto técnico (`ai_chat_message_feedback`) na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de feedback...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de feedback.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>CSAT</h4>
              <strong>{formatPercent(summary.csat)}</strong>
              <p>Feedback positivo ÷ total.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Positivos</h4>
              <strong>{formatNumber(summary.positiveCount)}</strong>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Negativos</h4>
              <strong>{formatNumber(summary.negativeCount)}</strong>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Perda de contexto</h4>
              <strong>{formatNumber(summary.lostContextCount)}</strong>
            </article>
          </div>

          {summary.alerts?.length ? (
            <article className="mdc-admin-kpi-card mdc-admin-kpi-card--wide">
              <h4>Alertas de qualidade</h4>
              <ul>
                {summary.alerts.map((alert) => (
                  <li key={alert.code}>{alert.message}</li>
                ))}
              </ul>
            </article>
          ) : null}

          <div className="mdc-admin-metrics-tab__split">
            <article className="mdc-admin-kpi-card">
              <h4>Top motivos negativos</h4>
              <ul>
                {(summary.feedbackByReason ?? []).slice(0, 8).map((row) => (
                  <li key={row.key}>
                    {row.key}: {formatNumber(row.count)}
                  </li>
                ))}
              </ul>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Por intenção</h4>
              <ul>
                {(summary.feedbackByIntent ?? []).slice(0, 8).map((row) => (
                  <li key={row.key}>
                    {row.key}: {formatNumber(row.count)}
                  </li>
                ))}
              </ul>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Por agente</h4>
              <ul>
                {(summary.feedbackByAgent ?? []).slice(0, 8).map((row) => (
                  <li key={row.key}>
                    {row.key}: {formatNumber(row.count)}
                  </li>
                ))}
              </ul>
            </article>
          </div>
        </>
      ) : null}
    </section>
  );
}
