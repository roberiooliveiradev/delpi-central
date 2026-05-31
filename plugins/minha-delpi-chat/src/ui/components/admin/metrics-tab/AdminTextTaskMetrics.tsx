import type { AdminTextTaskSummary } from "../../../../data/api/adminTypes";

type AdminTextTaskMetricsProps = {
  summary: AdminTextTaskSummary | null;
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

export function AdminTextTaskMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminTextTaskMetricsProps) {
  const subtypeEntries = summary
    ? Object.entries(summary.bySubtype).sort((left, right) => right[1] - left[1])
    : [];

  return (
    <section
      className="mdc-admin-drawing-metrics"
      aria-labelledby="mdc-admin-text-task-metrics-title"
    >
      <header className="mdc-admin-drawing-metrics__header">
        <div>
          <p className="mdc-chat-eyebrow">Playbook 03</p>
          <h3 id="mdc-admin-text-task-metrics-title">Especialista em textos</h3>
          <p>
            Agregado de snapshots em auditoria (`metadata.textTaskMetrics`) na janela de{" "}
            {summary?.windowHours ?? windowHours}h.
          </p>
        </div>
      </header>

      {isLoading ? (
        <p className="mdc-chat-muted">Carregando métricas textuais...</p>
      ) : null}

      {!isLoading && !summary ? (
        <p className="mdc-chat-muted">Não foi possível carregar o resumo textual.</p>
      ) : null}

      {summary ? (
        <>
          <div className="mdc-admin-kpi-grid mdc-admin-drawing-metrics__grid">
            <article className="mdc-admin-kpi-card">
              <h4>Tarefas textuais</h4>
              <strong>{formatNumber(summary.textTasksCount)}</strong>
              <p>Turnos com snapshot textual na janela.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Mistas</h4>
              <strong>{formatNumber(summary.mixedTurnCount)}</strong>
              <p>Consulta operacional + redação no mesmo fluxo.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Qualidade</h4>
              <strong>{formatNumber(summary.qualityFailedCount)}</strong>
              <p>Respostas com falha no validador textual.</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Lousa versionada</h4>
              <strong>{formatNumber(summary.canvasVersionedCount)}</strong>
              <p>Atualizações com histórico de versões na lousa.</p>
            </article>
          </div>

          {subtypeEntries.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list">
              <h4>Por subtipo</h4>
              <ul>
                {subtypeEntries.map(([subtype, count]) => (
                  <li key={subtype}>
                    <span>{subtype}</span>
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
                    <th>Subtipo</th>
                    <th>Tipo</th>
                    <th>Misto</th>
                  </tr>
                </thead>
                <tbody>
                  {summary.recent.map((item, index) => (
                    <tr key={`${item.loggedAt}-${index}`}>
                      <td>{formatLoggedAt(item.loggedAt)}</td>
                      <td>{item.subtype ?? "—"}</td>
                      <td>{item.type ?? "—"}</td>
                      <td>{item.mixed ? "sim" : "—"}</td>
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
