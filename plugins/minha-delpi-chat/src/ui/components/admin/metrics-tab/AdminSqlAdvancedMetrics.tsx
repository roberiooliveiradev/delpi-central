import type { AdminSqlAdvancedSummary } from "../../../../data/api/adminTypes";

type AdminSqlAdvancedMetricsProps = {
  summary: AdminSqlAdvancedSummary | null;
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

function formatModeLabel(mode?: string | null): string {
  const labels: Record<string, string> = {
    create: "Criação",
    review: "Revisão",
    explain: "Explicação",
    optimize: "Otimização",
    execute: "Execução",
    schema_explore: "Schema",
    incremental_edit: "Edição incremental",
    analyze_result: "Análise de resultado",
    visualize: "Visualização",
  };

  if (!mode) {
    return "—";
  }

  return labels[mode] ?? mode;
}

export function AdminSqlAdvancedMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminSqlAdvancedMetricsProps) {
  const modeEntries = summary
    ? Object.entries(summary.byMode).sort((left, right) => right[1] - left[1])
    : [];
  const dialectEntries = summary
    ? Object.entries(summary.byDialect).sort((left, right) => right[1] - left[1])
    : [];
  const chartEntries = summary?.byChartType
    ? Object.entries(summary.byChartType).sort((left, right) => right[1] - left[1])
    : [];

  return (
    <section
      className="mdc-admin-drawing-metrics mdc-admin-sql-advanced-metrics"
      aria-labelledby="mdc-admin-sql-advanced-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Especialista SQL</p>
          <h3 id="mdc-admin-sql-advanced-metrics-title">SQL Avançado</h3>
          <p>
            Agregado de snapshots em auditoria (`metadata.sqlAdvancedMetrics`) na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? <p className="mdc-chat-muted">Carregando métricas SQL...</p> : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo do especialista SQL.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Turnos SQL</h4>
              <strong>{formatNumber(summary.runsCount)}</strong>
              <p>Conversas com skill SQL avançada ativa.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Bloqueios</h4>
              <strong>{formatNumber(summary.blockedCount)}</strong>
              <p>Comandos destrutivos detectados e recusados.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Resultados vazios</h4>
              <strong>{formatNumber(summary.emptyResultCount)}</strong>
              <p>Execuções sem linhas retornadas.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Edição incremental</h4>
              <strong>{formatNumber(summary.incrementalEditCount)}</strong>
              <p>Turnos com query ativa pronta para refinamento.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>CTEs / Window</h4>
              <strong>
                {formatNumber(summary.cteUsageCount)} / {formatNumber(summary.windowFunctionUsageCount)}
              </strong>
              <p>Uso detectado em SQL gerado ou analisado.</p>
            </article>

            <article className="mdc-admin-kpi-card">
              <h4>Prefetch schema</h4>
              <strong>{formatNumber(summary.schemaPrefetchCount)}</strong>
              <p>Turnos que recomendaram explorar `/system/tables/*`.</p>
            </article>
          </div>

          {modeEntries.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Por modo</h4>
              <ul>
                {modeEntries.map(([mode, count]) => (
                  <li key={mode}>
                    <span>{formatModeLabel(mode)}</span>
                    <strong>{formatNumber(count)}</strong>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {dialectEntries.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Por dialeto</h4>
              <ul>
                {dialectEntries.map(([dialect, count]) => (
                  <li key={dialect}>
                    <span>{dialect}</span>
                    <strong>{formatNumber(count)}</strong>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {chartEntries.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Visualização sugerida</h4>
              <ul>
                {chartEntries.map(([chartType, count]) => (
                  <li key={chartType}>
                    <span>{chartType}</span>
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
                    <th>Modo</th>
                    <th>Dialeto</th>
                    <th>Bloqueado</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent.map((item, index) => (
                    <tr key={`${item.loggedAt ?? index}-${item.mode ?? "mode"}`}>
                      <td>{formatLoggedAt(item.loggedAt)}</td>
                      <td>{formatModeLabel(item.mode)}</td>
                      <td>{item.dialect ?? "—"}</td>
                      <td>{item.blocked ? "Sim" : "Não"}</td>
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
