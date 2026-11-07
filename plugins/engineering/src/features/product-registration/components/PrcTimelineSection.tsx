/** Histórico do caso — ledger append-only mapeado para
 * EngineeringTimeline (ordem real de sequence_number). */

import { EngineeringTimeline } from "../../../ui/engineeringUi";
import type { PrcTimelineEvent } from "../api/productRegistrationApi";
import {
  PRC_EVENT_LABELS,
  prcPersonLabel,
  prcStatusLabel,
} from "../prcCopy";

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function actorLabel(subject: string): string {
  return UUID_RE.test(subject)
    ? "Ator registrado no Portal"
    : subject || prcPersonLabel(null);
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
        occurredAt: ev.occurred_at,
        timeLabel: new Date(ev.occurred_at).toLocaleString("pt-BR"),
        detail: (
          <>
            {transition ? <span>{transition} · </span> : null}
            {ev.reason ? <span>{ev.reason}</span> : null}
          </>
        ),
        meta: `${actorLabel(ev.actor_subject)}${channel ? ` · canal ${channel}` : ""}`,
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
