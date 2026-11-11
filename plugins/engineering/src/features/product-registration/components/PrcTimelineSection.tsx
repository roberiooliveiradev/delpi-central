/** Histórico do caso — ledger append-only mapeado para
 * EngineeringTimeline (ordem real de sequence_number). */

import {
  EngineeringInitialsAvatar,
  EngineeringTimeline,
} from "../../../ui/engineeringUi";
import type { PrcTimelineEvent } from "../api/productRegistrationApi";
import { prcTimelineItemViews } from "@delpi/plugin-ui/index";

export function PrcTimelineSection({
  events,
  loading,
}: {
  events: PrcTimelineEvent[];
  loading?: boolean;
}) {
  const items = prcTimelineItemViews(events).map((v) => ({
    id: v.id,
    title: v.title,
    marker: <EngineeringInitialsAvatar name={v.actorLabel} size="sm" />,
    occurredAt: v.occurredAt,
    timeLabel: v.timeLabel,
    detail: (
      <>
        {v.transition ? <span>{v.transition} · </span> : null}
        {v.reasonText ? <span>{v.reasonText}</span> : null}
      </>
    ),
    meta: v.metaText,
  }));

  return (
    <EngineeringTimeline
      items={items}
      loading={loading}
      emptyMessage="Nenhum evento registrado para esta solicitação."
      aria-label="Histórico de atendimento da solicitação"
    />
  );
}
