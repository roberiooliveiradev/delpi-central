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

function formatPercent(rate?: number | null): string {
  if (typeof rate !== "number") {
    return "—";
  }

  return new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 1,
  }).format(rate);
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

function DistributionList({
  title,
  items,
  emptyLabel,
}: {
  title: string;
  items: { label: string; count: number }[];
  emptyLabel: string;
}) {
  return (
    <article className="mdc-admin-kpi-card">
      <h4>{title}</h4>
      {!items.length ? (
        <p className="mdc-chat-muted">{emptyLabel}</p>
      ) : (
        <ul className="mdc-admin-distribution-list">
          {items.map((item) => (
            <li key={item.label}>
              <span>{item.label}</span>
              <strong>{formatNumber(item.count)}</strong>
            </li>
          ))}
        </ul>
      )}
    </article>
  );
}

export function AdminPresentationMetrics({
  summary,
  isLoading = false,
  windowHours,
}: AdminPresentationMetricsProps) {
  const alerts = summary?.alerts ?? [];
  const topSelected = summary?.topSelected ?? [];
  const topEvents = summary?.topEvents ?? [];
  const recentEvents = summary?.recentEvents ?? [];

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
          {alerts.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__status-list" role="status">
              <h4>Alertas</h4>
              <ul>
                {alerts.map((alert) => (
                  <li key={alert}>{alert}</li>
                ))}
              </ul>
            </div>
          ) : null}

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
              <h4>Engajamento</h4>
              <strong>{formatPercent(summary.engagementRate)}</strong>
              <p>Eventos por resposta rica (média na janela).</p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Troca de formato</h4>
              <strong>{formatNumber(summary.viewSwitchCount)}</strong>
              <p>
                {formatPercent(summary.viewSwitchRate)} das respostas — texto ↔ tabela ↔ gráfico.
              </p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>→ Tabela</h4>
              <strong>{formatNumber(summary.switchToTableCount)}</strong>
              <p>
                {formatPercent(summary.switchToTableRate)} das trocas de vista foram para tabela.
              </p>
            </article>
            <article className="mdc-admin-kpi-card">
              <h4>Alteração de eixo</h4>
              <strong>{formatNumber(summary.axisChangeCount)}</strong>
              <p>{formatPercent(summary.axisChangeRate)} das respostas ricas.</p>
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
            <DistributionList
              title="Formatos escolhidos (API)"
              items={topSelected}
              emptyLabel="Sem dados na janela."
            />
            <DistributionList
              title="Eventos mais frequentes"
              items={topEvents}
              emptyLabel="Sem interações na janela."
            />
            <DistributionList
              title="Destino das trocas de vista"
              items={summary.topViewTargets ?? []}
              emptyLabel="Sem trocas de vista."
            />
            <DistributionList
              title="Colunas de eixo alteradas"
              items={summary.topAxisColumns ?? []}
              emptyLabel="Sem alterações de eixo."
            />
            <DistributionList
              title="Filtros por categoria"
              items={summary.topFilterKeys ?? []}
              emptyLabel="Sem filtros de categoria."
            />
          </div>

          {recentEvents.length > 0 ? (
            <div className="mdc-admin-drawing-metrics__table-wrap">
              <table className="mdc-admin-drawing-metrics__table">
                <thead>
                  <tr>
                    <th>Quando</th>
                    <th>Evento</th>
                    <th>De → Para</th>
                    <th>Detalhe</th>
                  </tr>
                </thead>
                <tbody>
                  {recentEvents.map((row, index) => {
                    const event = String(row.event ?? "—");
                    const from = row.from != null ? String(row.from) : "";
                    const to = row.to != null ? String(row.to) : "";
                    const transition =
                      from || to ? `${from || "—"} → ${to || "—"}` : "—";
                    const detail =
                      row.column != null
                        ? String(row.column)
                        : row.filterKey != null
                          ? `${row.filterKey}=${row.filterValue ?? ""}`
                          : "—";

                    return (
                      <tr key={`${row.loggedAt}-${event}-${index}`}>
                        <td>{formatLoggedAt(row.loggedAt as string | undefined)}</td>
                        <td>{event}</td>
                        <td>{transition}</td>
                        <td>{detail}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : null}
        </>
      ) : null}
    </section>
  );
}
