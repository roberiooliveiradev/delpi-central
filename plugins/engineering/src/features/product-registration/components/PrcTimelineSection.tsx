/** Histórico do caso — ledger append-only mapeado para
 * EngineeringTimeline (ordem real de sequence_number). */

import {
  EngineeringInitialsAvatar,
  EngineeringTimeline,
} from "../../../ui/engineeringUi";
import type { PrcTimelineEvent } from "../api/productRegistrationApi";
import {
  PRC_EVENT_LABELS,
  prcPersonLabel,
  prcStatusLabel,
} from "../prcCopy";

function actorLabel(ev: PrcTimelineEvent): string {
  const name = (ev.actor_display_name || "").trim();
  if (name) return name;
  return prcPersonLabel(ev.actor_subject, null);
}

export function PrcTimelineSection({
  events,
  loading,
}: {
  events: PrcTimelineEvent[];
  loading?: boolean;
}) {
  const items = [...events]
    .sort((a, b) => a.sequence_number - b.sequence_number)
    .map((ev) => {
      const transition =
        ev.previous_status && ev.next_status
          ? `${prcStatusLabel(ev.previous_status)} → ${prcStatusLabel(ev.next_status)}`
          : ev.next_status
            ? prcStatusLabel(ev.next_status)
            : null;
      const channel =
        typeof ev.metadata?.channel === "string" ? ev.metadata.channel : null;
      return {
        id: ev.id,
        title: PRC_EVENT_LABELS[ev.event_type] || ev.event_type,
        marker: (
          <EngineeringInitialsAvatar name={actorLabel(ev)} size="sm" />
        ),
        occurredAt: ev.occurred_at,
        timeLabel: new Date(ev.occurred_at).toLocaleString("pt-BR"),
        detail: (
          <>
            {transition ? <span>{transition} · </span> : null}
            {ev.reason ? <span>{ev.reason}</span> : null}
          </>
        ),
        meta: `${actorLabel(ev)}${ev.actor_email ? ` · ${ev.actor_email}` : ""}${channel ? ` · canal ${channel}` : ""}`,
      };
    });

  return (
    <EngineeringTimeline
      items={items}
      loading={loading}
      emptyMessage="Nenhum evento registrado para esta solicitação."
      aria-label="Histórico de atendimento da solicitação"
    />
  );
}
