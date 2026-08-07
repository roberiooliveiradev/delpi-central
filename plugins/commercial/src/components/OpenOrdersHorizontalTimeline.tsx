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
      {points.map((point, index) => (
        <li
          key={point.id}
          className={[
            "cm-op-htimeline__item",
            `cm-op-htimeline__item--${point.tone}`,
            point.kind === "today" ? "cm-op-htimeline__item--today" : "",
            point.isCurrent ? "cm-op-htimeline__item--current" : "",
          ]
            .filter(Boolean)
            .join(" ")}
        >
          {index > 0 ? <span className="cm-op-htimeline__connector" aria-hidden="true" /> : null}
          <span className="cm-op-htimeline__dot" aria-hidden="true" />
          <span className="cm-op-htimeline__label">{point.label}</span>
          <time className="cm-op-htimeline__date" dateTime={point.dateIso}>
            {point.dateLabel}
          </time>
          {point.isCurrent ? (
            <span className="cm-op-htimeline__current-tag">Atual</span>
          ) : null}
          {point.kind === "today" ? (
            <span className="cm-op-htimeline__today-tag">Agora</span>
          ) : null}
        </li>
      ))}
    </ol>
  );
}
