import { Flag } from "lucide-react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type HorizontalTimelineTone = "neutral" | "info" | "success" | "warning" | "danger";

export type HorizontalTimelinePoint = {
  id: string;
  label: string;
  dateIso: string;
  dateLabel: string;
  tone: HorizontalTimelineTone;
  /** Marco «hoje» — usa bandeira e tag de agora. */
  kind?: "event" | "today";
  /** Destaque de posição atual (ex.: último marco passado). */
  isCurrent?: boolean;
};

export type HorizontalTimelineClassNames = {
  root: string;
  item: string;
  connector: string;
  dot: string;
  flag: string;
  label: string;
  date: string;
  currentTag: string;
  todayTag: string;
  empty: string;
};

export type HorizontalTimelineLabels = {
  currentTag: string;
  todayTag: string;
  emptyMessage: string;
  todayMarkerTitle: string;
};

export const DEFAULT_HORIZONTAL_TIMELINE_LABELS: HorizontalTimelineLabels = {
  currentTag: "Atual",
  todayTag: "Agora",
  emptyMessage: "Sem marcos com data.",
  todayMarkerTitle: "Hoje",
};

export type HorizontalTimelineProps = {
  classNames: HorizontalTimelineClassNames;
  points: HorizontalTimelinePoint[];
  labels?: Partial<HorizontalTimelineLabels>;
  className?: string;
  "aria-label"?: string;
};

export function horizontalTimelineBemClasses(prefix: string): HorizontalTimelineClassNames {
  const block = `${prefix}-htimeline`;
  return {
    root: delpiUiClass(block, "delpi-ui-htimeline"),
    item: delpiUiClass(`${block}__item`, "delpi-ui-htimeline__item"),
    connector: delpiUiClass(`${block}__connector`, "delpi-ui-htimeline__connector"),
    dot: delpiUiClass(`${block}__dot`, "delpi-ui-htimeline__dot"),
    flag: delpiUiClass(`${block}__flag`, "delpi-ui-htimeline__flag"),
    label: delpiUiClass(`${block}__label`, "delpi-ui-htimeline__label"),
    date: delpiUiClass(`${block}__date`, "delpi-ui-htimeline__date"),
    currentTag: delpiUiClass(`${block}__current-tag`, "delpi-ui-htimeline__current-tag"),
    todayTag: delpiUiClass(`${block}__today-tag`, "delpi-ui-htimeline__today-tag"),
    empty: delpiUiClass(`${block}__empty`, "delpi-ui-htimeline__empty"),
  };
}

/**
 * Linha do tempo horizontal de marcos (datas + tom + opcional «hoje» com bandeira).
 */
export function HorizontalTimeline({
  classNames,
  points,
  labels: labelsProp,
  className,
  "aria-label": ariaLabel = "Linha do tempo",
}: HorizontalTimelineProps) {
  const labels = { ...DEFAULT_HORIZONTAL_TIMELINE_LABELS, ...labelsProp };

  if (points.length === 0) {
    return <p className={classNames.empty}>{labels.emptyMessage}</p>;
  }

  return (
    <ol className={[classNames.root, className].filter(Boolean).join(" ")} aria-label={ariaLabel}>
      {points.map((point, index) => {
        const isToday = point.kind === "today";
        const modifiers = [
          point.tone,
          ...(isToday ? (["today"] as const) : []),
          ...(point.isCurrent ? (["current"] as const) : []),
        ];
        const itemBases = classNames.item.split(/\s+/).filter(Boolean);
        const itemClass = [
          ...itemBases,
          ...modifiers.flatMap((mod) => itemBases.map((base) => `${base}--${mod}`)),
        ].join(" ");

        return (
          <li key={point.id} className={itemClass}>
            {index > 0 ? <span className={classNames.connector} aria-hidden="true" /> : null}
            {isToday ? (
              <span className={classNames.flag} title={labels.todayMarkerTitle} aria-hidden="true">
                <Flag size={14} strokeWidth={2.4} aria-hidden="true" />
              </span>
            ) : (
              <span className={classNames.dot} aria-hidden="true" />
            )}
            <span className={classNames.label}>{point.label}</span>
            <time className={classNames.date} dateTime={point.dateIso}>
              {point.dateLabel}
            </time>
            {point.isCurrent ? (
              <span className={classNames.currentTag}>{labels.currentTag}</span>
            ) : null}
            {isToday ? (
              <span className={classNames.todayTag}>
                <Flag size={10} strokeWidth={2.5} aria-hidden="true" />
                {labels.todayTag}
              </span>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

export type DashboardHorizontalTimelineProps = Omit<HorizontalTimelineProps, "classNames">;

export function createDashboardHorizontalTimeline(config: { prefix: string }) {
  const classNames = horizontalTimelineBemClasses(config.prefix);
  return function DashboardHorizontalTimeline(props: DashboardHorizontalTimelineProps) {
    return <HorizontalTimeline classNames={classNames} {...props} />;
  };
}
