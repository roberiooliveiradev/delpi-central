import { useEffect, useState } from "react";

import { listEvents } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import type { TimelineEvent } from "../types/requests";

type TimelinePanelProps = {
  requestId: string;
};

export function TimelinePanel({ requestId }: TimelinePanelProps) {
  const [items, setItems] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const ac = new AbortController();
    listEvents(requestId, { signal: ac.signal })
      .then((data) => setItems(data.items || []))
      .catch((err: Error) => {
        if (err.name !== "AbortError") setError(err.message);
      });
    return () => ac.abort();
  }, [requestId]);

  return (
    <section
      className="dashboard-my-requests__panel"
      data-help="timeline"
      title={MY_REQUESTS_HELP_TOOLTIPS.timeline.section}
    >
      <h2>Linha do tempo</h2>
      {error ? <p className="dashboard-my-requests__error">{error}</p> : null}
      {!error && items.length === 0 ? (
        <p className="dashboard-my-requests__muted">Sem eventos ainda.</p>
      ) : null}
      <ul className="dashboard-my-requests__list">
        {items.map((item) => (
          <li key={item.id}>
            <strong>{item.event_type}</strong>
            {item.actor_name ? ` — ${item.actor_name}` : ""}
            {item.created_at ? (
              <span className="dashboard-my-requests__muted"> · {item.created_at}</span>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
