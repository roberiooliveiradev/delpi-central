import { Flag } from "lucide-react";

import type { OpHorizontalTimelinePoint } from "../utils/opTimeline";

type OpenOrdersHorizontalTimelineProps = {
  points: OpHorizontalTimelinePoint[];
  emptyMessage?: string;
  "aria-label"?: string;
};

export function OpenOrdersHorizontalTimeline({
  points,
  emptyMessage = "Sem marcos com data.",
  "aria-label": ariaLabel = "Linha do tempo horizontal da OP",
}: OpenOrdersHorizontalTimelineProps) {
  if (points.length === 0) {
    return <p className="cm-open-orders-detail__muted">{emptyMessage}</p>;
  }

  return (
    <ol className="cm-op-htimeline" aria-label={ariaLabel}>
      {points.map((point, index) => {
        const isToday = point.kind === "today";
        return (
          <li
            key={point.id}
            className={[
              "cm-op-htimeline__item",
              `cm-op-htimeline__item--${point.tone}`,
              isToday ? "cm-op-htimeline__item--today" : "",
              point.isCurrent ? "cm-op-htimeline__item--current" : "",
            ]
              .filter(Boolean)
              .join(" ")}
          >
            {index > 0 ? <span className="cm-op-htimeline__connector" aria-hidden="true" /> : null}
            {isToday ? (
              <span className="cm-op-htimeline__flag" title="Hoje" aria-hidden="true">
                <Flag size={14} strokeWidth={2.4} aria-hidden="true" />
              </span>
            ) : (
              <span className="cm-op-htimeline__dot" aria-hidden="true" />
            )}
            <span className="cm-op-htimeline__label">{point.label}</span>
            <time className="cm-op-htimeline__date" dateTime={point.dateIso}>
              {point.dateLabel}
            </time>
            {point.isCurrent ? (
              <span className="cm-op-htimeline__current-tag">Atual</span>
            ) : null}
            {isToday ? (
              <span className="cm-op-htimeline__today-tag">
                <Flag size={10} strokeWidth={2.5} aria-hidden="true" />
                Agora
              </span>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}
