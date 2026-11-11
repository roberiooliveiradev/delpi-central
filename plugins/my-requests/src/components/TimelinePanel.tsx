import { useEffect, useMemo, useState } from "react";

import { listEvents } from "../api/requestsApi";
import { RequestHistoryTimeline } from "./RequestHistoryTimeline";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import {
  formatDateTimePtBr,
  timelineEventJustification,
  timelineEventTitle,
} from "../content/presentationLabels";
import { useParticipantAvatarUrls } from "../hooks/useParticipantAvatarUrls";
import type { TimelineEvent } from "../types/requests";
import { MyRequestsSectionCard } from "../ui/mrUi";

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

  const actorIds = useMemo(
    () => items.map((item) => item.actor_user_id),
    [items],
  );
  const avatarByUserId = useParticipantAvatarUrls(actorIds);

  const timelineItems = useMemo(
    () =>
      items.map((item) => ({
        id: item.id,
        title: timelineEventTitle(item),
        occurredAt: item.created_at || undefined,
        timeLabel: formatDateTimePtBr(item.created_at),
        actorName: (item.actor_name || "").trim() || null,
        actorUserId: (item.actor_user_id || "").trim() || null,
        detailText: timelineEventJustification(item.payload),
      })),
    [items],
  );

  return (
    <MyRequestsSectionCard
      title="Linha do tempo"
      hint={MY_REQUESTS_HELP_TOOLTIPS.timeline.section}
    >
      <div data-help="timeline">
        <RequestHistoryTimeline
          items={timelineItems}
          avatarByUserId={avatarByUserId}
          error={error}
        />
      </div>
    </MyRequestsSectionCard>
  );
}
