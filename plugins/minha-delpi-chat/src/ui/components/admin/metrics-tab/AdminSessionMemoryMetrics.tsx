import type { AdminSessionMemorySummary } from "../../../../data/api/adminTypes";

type AdminSessionMemoryMetricsProps = {
  summary: AdminSessionMemorySummary | null;
  isLoading?: boolean;
  windowHours: number;
};

function formatNumber(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR").format(value);
}

function formatRate(value?: number | null): string {
  if (typeof value !== "number") {
    return "—";
  }

  return `${Math.round(value * 100)}%`;
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

export function AdminSessionMemoryMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminSessionMemoryMetricsProps) {
  const flagRows = summary?.assertivenessFlags ?? [];
  const feedback = summary?.feedback;
  const alerts = summary?.alerts ?? [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-session-memory-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Memória de sessão</p>
          <h3 id="mdc-admin-session-memory-metrics-title">Contexto e assertividade</h3>
          <p>
            Agregado de `sessionMemoryAdminMetrics` e feedback de memória na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas de memória...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo de memória.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Turnos com memória</h4>
              <strong>{formatNumber(summary.memoryTurnsCount)}</strong>
              <p>Respostas com snapshot de memória na auditoria.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Follow-ups</h4>
              <strong>{formatNumber(summary.followUpTurns)}</strong>
              <p>Taxa de resolução: {formatRate(summary.followUpResolutionRate)}.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Risco de perda</h4>
              <strong>{formatNumber(summary.contextLossRiskTurns)}</strong>
              <p>Turnos com assertividade baixa ou entidade não reutilizada.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Assertividade &lt; 70</h4>
              <strong>{formatNumber(summary.lowAssertivenessTurns)}</strong>
              <p>Turnos com score contextual abaixo do limiar.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Ambiguidade</h4>
              <strong>{formatNumber(summary.ambiguityTurns)}</strong>
              <p>Memória não resolveu referência sozinha.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Feedback memória</h4>
              <strong>{formatNumber(feedback?.memoryFeedbackCount)}</strong>
              <p>
                Perda de contexto reportada:{" "}
                {formatNumber(feedback?.lostContextFeedbackCount)}.
              </p>
            </article>
          </div>

          {alerts.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Alertas</h4>
              <ul>
                {alerts.map((alert) => (
                  <li key={alert.code}>
                    <strong>{alert.code}</strong> — {alert.message}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {flagRows.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Flags de assertividade</h4>
              <ul>
                {flagRows.map((row) => (
                  <li key={row.key}>
                    <span>{row.key}</span>
                    <strong>{formatNumber(row.count)}</strong>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {summary.recent.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Turnos recentes</h4>
              <ul>
                {summary.recent.map((item, index) => (
                  <li key={`${item.loggedAt ?? index}-${index}`}>
                    <span>{formatLoggedAt(item.loggedAt)}</span>
                    <span>
                      score {item.assertivenessScore ?? "—"}
                      {item.contextLossRisk ? " · risco" : ""}
                      {item.followUpDetected ? " · follow-up" : ""}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
