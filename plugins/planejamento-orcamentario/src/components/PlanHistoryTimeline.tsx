type PlanHistoryTimelineEntry = {
  id: string;
  action: string;
  previous_status?: string | null;
  new_status: string;
  comment?: string | null;
  actor_sub: string;
  actor_name?: string | null;
  created_at: string;
};

type PlanHistoryTimelineProps = {
  items: PlanHistoryTimelineEntry[];
  emptyMessage?: string;
  actionLabel: (action?: string | null) => string;
  statusLabel: (status?: string | null) => string;
  formatDateTime: (value?: string | null) => string;
};

/** Timeline genérica de workflow (CAPEX / Pessoal). */
export function PlanHistoryTimeline({
  items,
  emptyMessage = "Nenhum evento de histórico registrado ainda.",
  actionLabel,
  statusLabel,
  formatDateTime,
}: PlanHistoryTimelineProps) {
  if (!items.length) {
    return <p className="po-muted">{emptyMessage}</p>;
  }

  return (
    <ol className="po-timeline">
      {items.map((entry) => (
        <li key={entry.id} className="po-timeline__item">
          <span className="po-timeline__marker" aria-hidden="true" />
          <div className="po-timeline__body">
            <div className="po-timeline__head">
              <strong>{actionLabel(entry.action)}</strong>
              <span className="po-timeline__date">{formatDateTime(entry.created_at)}</span>
            </div>
            <dl className="po-detail-grid">
              <div>
                <dt>Status anterior</dt>
                <dd>
                  {entry.previous_status ? statusLabel(entry.previous_status) : "—"}
                </dd>
              </div>
              <div>
                <dt>Novo status</dt>
                <dd>{statusLabel(entry.new_status)}</dd>
              </div>
              <div>
                <dt>Usuário</dt>
                <dd>{entry.actor_name?.trim() || entry.actor_sub || "—"}</dd>
              </div>
            </dl>
            {entry.comment?.trim() ? (
              <p className="po-muted" style={{ marginTop: 8 }}>
                Comentário: {entry.comment}
              </p>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
