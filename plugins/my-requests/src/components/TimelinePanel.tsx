import { useEffect, useMemo, useState } from "react";

import { listEvents } from "../api/requestsApi";
import { PersonIdentity } from "./PersonIdentity";
import { MY_REQUESTS_HELP_TOOLTIPS } from "../content/helpTooltips";
import { eventLabel, formatDateTimePtBr } from "../content/presentationLabels";
import { useParticipantAvatarUrls } from "../hooks/useParticipantAvatarUrls";
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

  const actorIds = useMemo(
    () => items.map((item) => item.actor_user_id),
    [items],
  );
  const avatarByUserId = useParticipantAvatarUrls(actorIds);

  const timelineItems = useMemo(
    () =>
      items.map((item) => {
        const name = (item.actor_name || "").trim();
        const userId = (item.actor_user_id || "").trim();
        return {
          id: item.id,
          title: eventLabel(item.event_type),
          occurredAt: item.created_at || undefined,
          timeLabel: formatDateTimePtBr(item.created_at),
          detail:
            name || userId ? (
              <PersonIdentity
                name={name || null}
                userId={userId || null}
                src={userId ? avatarByUserId.get(userId) || null : null}
              />
            ) : undefined,
        };
      }),
    [items, avatarByUserId],
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
