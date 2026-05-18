import type { AdminAuditTimelineDay } from "../../../../data/api/adminTypes";

import "./AuditTimelinePanel.css";

type AuditTimelinePanelProps = {
  days: AdminAuditTimelineDay[];
  onSelectLog?: (logId: number) => void;
  onFilterByTrace?: (traceId: string) => void;
};

export function AuditTimelinePanel({ days, onSelectLog, onFilterByTrace }: AuditTimelinePanelProps) {
  if (days.length === 0) {
    return <p className="mdc-chat-muted">Nenhum evento na timeline para os filtros atuais.</p>;
  }

  return (
    <section className="mdc-audit-timeline" aria-label="Timeline de auditoria">
      {days.map((day) => (
        <article key={day.date} className="mdc-audit-timeline__day">
          <header>
            <h3>{new Date(`${day.date}T12:00:00`).toLocaleDateString("pt-BR")}</h3>
            <strong>{day.total} evento(s)</strong>
          </header>

          {day.actions.length > 0 ? (
            <ul className="mdc-audit-timeline__actions">
              {day.actions.map((item) => (
                <li key={`${day.date}-${item.action}`}>
                  <span>{item.action}</span>
                  <strong>{item.count}</strong>
                </li>
              ))}
            </ul>
          ) : null}

          {day.recent.length > 0 ? (
            <ul className="mdc-audit-timeline__recent">
              {day.recent.map((log) => (
                <li key={log.id}>
                  <button
                    type="button"
                    onClick={() => {
                      if (log.traceId && onFilterByTrace) {
                        onFilterByTrace(log.traceId);
                        return;
                      }

                      onSelectLog?.(log.id);
                    }}
                  >
                    <strong>{log.action}</strong>
                    <span>{new Date(log.createdAt).toLocaleTimeString("pt-BR")}</span>
                    {log.traceId ? <small>trace: {log.traceId.slice(0, 12)}…</small> : null}
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
        </article>
      ))}
    </section>
  );
}
