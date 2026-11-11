/** PRC-REF-023-UI-FIX-04 — renderer único de histórico de Minhas
 * Solicitações. Recebe itens já normalizados por origem (Requests API
 * ou Engineering API via `prcTimelineItemViews`) e renderiza o mesmo
 * padrão visual: PersonIdentity + justificativa + transição sobre
 * MyRequestsTimeline. Não consulta APIs e não conhece a fonte. */

import { PersonIdentity } from "./PersonIdentity";
import {
  MyRequestsEmptyState,
  MyRequestsStateBanner,
  MyRequestsTimeline,
} from "../ui/mrUi";

export type RequestHistoryItemView = {
  id: string;
  title: string;
  occurredAt?: string;
  timeLabel: string;
  /** Identidade do responsável (resolvida por PersonIdentity). */
  actorName?: string | null;
  actorUserId?: string | null;
  /** Texto secundário: justificativa/motivo do evento. */
  detailText?: string | null;
  /** Transição de status, quando a origem a informa. */
  transition?: string | null;
  /** Detalhe secundário adicional (ex.: e-mail/canal). */
  metaText?: string | null;
};

type Props = {
  items: RequestHistoryItemView[];
  /** Mapa userId → URL de avatar, resolvido pelo consumidor. */
  avatarByUserId?: ReadonlyMap<string, string>;
  error?: string | null;
  emptyMessage?: string;
};

export function RequestHistoryTimeline({
  items,
  avatarByUserId,
  error,
  emptyMessage = "Ainda não há eventos registrados.",
}: Props) {
  const timelineItems = items.map((item) => {
    const userId = (item.actorUserId || "").trim();
    const name = (item.actorName || "").trim();
    return {
      id: item.id,
      title: item.title,
      occurredAt: item.occurredAt,
      timeLabel: item.timeLabel,
      detail:
        name || userId || item.detailText || item.transition || item.metaText ? (
          <div className="my-requests-timeline-detail">
            {name || userId ? (
              <PersonIdentity
                name={name || null}
                userId={userId || null}
                src={
                  userId ? avatarByUserId?.get(userId) || null : null
                }
              />
            ) : null}
            {item.transition ? (
              <p className="my-requests-timeline-detail__reason">
                {item.transition}
              </p>
            ) : null}
            {item.detailText ? (
              <p className="my-requests-timeline-detail__reason">
                {item.detailText}
              </p>
            ) : null}
            {item.metaText ? (
              <p className="my-requests-timeline-detail__reason">
                {item.metaText}
              </p>
            ) : null}
          </div>
        ) : undefined,
    };
  });

  return (
    <>
      {error ? (
        <MyRequestsStateBanner variant="error">
          {error}
        </MyRequestsStateBanner>
      ) : null}
      {!error && items.length === 0 ? (
        <MyRequestsEmptyState message={emptyMessage} />
      ) : null}
      {timelineItems.length > 0 ? (
        <MyRequestsTimeline items={timelineItems} />
      ) : null}
    </>
  );
}
