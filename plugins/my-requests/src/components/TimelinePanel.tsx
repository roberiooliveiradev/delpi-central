import { useEffect, useMemo, useState } from "react";

import { listEvents } from "../api/requestsApi";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { eventLabel, formatDateTimePtBr } from "../content/presentationLabels";
import type { TimelineEvent } from "../types/requests";
import {
  MyRequestsEmptyState,
  MyRequestsSectionCard,
  MyRequestsStateBanner,
  MyRequestsTimeline,
} from "../ui/mrUi";

type TimelinePanelProps = {
  requestId: string;
  refreshKey?: number;
};

export function TimelinePanel({ requestId, refreshKey = 0 }: TimelinePanelProps) {
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
  }, [requestId, refreshKey]);

  const timelineItems = useMemo(
    () =>
      items.map((item) => ({
        id: item.id,
        title: eventLabel(item.event_type),
        occurredAt: item.created_at || undefined,
        timeLabel: formatDateTimePtBr(item.created_at),
        detail: item.actor_name || undefined,
      })),
    [items],
  );

  return (
    <MyRequestsSectionCard
      title="Linha do tempo"
      hint={MY_REQUESTS_HELP_TOOLTIPS.timeline.section}
    >
      <div data-help="timeline">
        {error ? (
          <MyRequestsStateBanner variant="error">{error}</MyRequestsStateBanner>
        ) : null}
        {!error && items.length === 0 ? (
          <MyRequestsEmptyState message="Ainda não há eventos registrados." />
        ) : null}
        {timelineItems.length > 0 ? <MyRequestsTimeline items={timelineItems} /> : null}
      </div>
    </MyRequestsSectionCard>
  );
}
