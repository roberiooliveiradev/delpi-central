import { Flag } from "lucide-react";
import { useMemo } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type HorizontalTimelineTone = "neutral" | "info" | "success" | "warning" | "danger";

export type HorizontalTimelinePoint = {
  id: string;
  label: string;
  dateIso: string;
  dateLabel: string;
  tone: HorizontalTimelineTone;
  /** Marco «hoje» — bandeira acima do trilho (não compete com marcos). */
  kind?: "event" | "today";
  /** Destaque de posição atual (ex.: último marco passado). */
  isCurrent?: boolean;
};

export type HorizontalTimelineClassNames = {
  root: string;
  track: string;
  rail: string;
  milestones: string;
  item: string;
  dot: string;
  caption: string;
  label: string;
  date: string;
  currentTag: string;
  now: string;
  flag: string;
  stem: string;
  pin: string;
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
    track: delpiUiClass(`${block}__track`, "delpi-ui-htimeline__track"),
    rail: delpiUiClass(`${block}__rail`, "delpi-ui-htimeline__rail"),
    milestones: delpiUiClass(`${block}__milestones`, "delpi-ui-htimeline__milestones"),
    item: delpiUiClass(`${block}__item`, "delpi-ui-htimeline__item"),
    dot: delpiUiClass(`${block}__dot`, "delpi-ui-htimeline__dot"),
    caption: delpiUiClass(`${block}__caption`, "delpi-ui-htimeline__caption"),
    label: delpiUiClass(`${block}__label`, "delpi-ui-htimeline__label"),
    date: delpiUiClass(`${block}__date`, "delpi-ui-htimeline__date"),
    currentTag: delpiUiClass(`${block}__current-tag`, "delpi-ui-htimeline__current-tag"),
    now: delpiUiClass(`${block}__now`, "delpi-ui-htimeline__now"),
    flag: delpiUiClass(`${block}__flag`, "delpi-ui-htimeline__flag"),
    stem: delpiUiClass(`${block}__stem`, "delpi-ui-htimeline__stem"),
    pin: delpiUiClass(`${block}__pin`, "delpi-ui-htimeline__pin"),
    todayTag: delpiUiClass(`${block}__today-tag`, "delpi-ui-htimeline__today-tag"),
    empty: delpiUiClass(`${block}__empty`, "delpi-ui-htimeline__empty"),
  };
}

function parseIsoDay(iso: string): number | null {
  const match = String(iso).trim().match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (!match) return null;
  const y = Number(match[1]);
  const m = Number(match[2]);
  const d = Number(match[3]);
  if (!y || !m || !d) return null;
  return Date.UTC(y, m - 1, d);
}

/** Posição 0–100 no eixo, com padding nas bordas para o marco não cortar. */
export function horizontalTimelinePositionPercent(
  dateIso: string,
  rangeStartMs: number,
  rangeEndMs: number,
  edgePadPercent = 6,
): number {
  const ms = parseIsoDay(dateIso);
  if (ms == null) return 50;
  const span = Math.max(rangeEndMs - rangeStartMs, 1);
  const raw = ((ms - rangeStartMs) / span) * 100;
  const padded = edgePadPercent + (raw / 100) * (100 - edgePadPercent * 2);
  return Math.min(100 - edgePadPercent, Math.max(edgePadPercent, padded));
}

type LaidOutEvent = HorizontalTimelinePoint & { leftPercent: number };

/**
 * Linha do tempo OTD: marcos no trilho (abaixo) + «Agora» como bandeira acima,
 * posicionada pela data (padrão swimlane / today-marker de dashboards industriais).
 */
export function HorizontalTimeline({
  classNames,
  points,
  labels: labelsProp,
  className,
  "aria-label": ariaLabel = "Linha do tempo",
}: HorizontalTimelineProps) {
  const labels = { ...DEFAULT_HORIZONTAL_TIMELINE_LABELS, ...labelsProp };

  const layout = useMemo(() => {
    const events = points.filter((p) => p.kind !== "today");
    const today = points.find((p) => p.kind === "today") ?? null;
    const dayMs = [
      ...events.map((p) => parseIsoDay(p.dateIso)),
      today ? parseIsoDay(today.dateIso) : null,
    ].filter((n): n is number => n != null);

    if (dayMs.length === 0) {
      return { events: [] as LaidOutEvent[], today: null as (LaidOutEvent & HorizontalTimelinePoint) | null };
    }

    const rangeStartMs = Math.min(...dayMs);
    const rangeEndMs = Math.max(...dayMs);

    const edgePad = 6;
    const laidEvents: LaidOutEvent[] = [...events]
      .sort((a, b) => a.dateIso.localeCompare(b.dateIso))
      .map((point) => ({
        ...point,
        leftPercent: horizontalTimelinePositionPercent(
          point.dateIso,
          rangeStartMs,
          rangeEndMs,
          edgePad,
        ),
      }));

    // Separação mínima entre marcos colados (ida + volta para caber nas bordas).
    // «Agora» não entra neste ajuste — permanece na % cronológica pura.
    const minGap = 7;
    const minLeft = edgePad;
    const maxLeft = 100 - edgePad;
    for (let i = 1; i < laidEvents.length; i += 1) {
      const prev = laidEvents[i - 1];
      const curr = laidEvents[i];
      if (curr.leftPercent - prev.leftPercent < minGap) {
        curr.leftPercent = prev.leftPercent + minGap;
      }
    }
    for (let i = laidEvents.length - 2; i >= 0; i -= 1) {
      const curr = laidEvents[i];
      const next = laidEvents[i + 1];
      if (next.leftPercent - curr.leftPercent < minGap) {
        curr.leftPercent = next.leftPercent - minGap;
      }
    }
    for (const event of laidEvents) {
      event.leftPercent = Math.min(maxLeft, Math.max(minLeft, event.leftPercent));
    }

    const todayLaid = today
      ? {
          ...today,
          leftPercent: horizontalTimelinePositionPercent(
            today.dateIso,
            rangeStartMs,
            rangeEndMs,
            edgePad,
          ),
        }
      : null;

    return { events: laidEvents, today: todayLaid };
  }, [points]);

  if (points.length === 0 || (layout.events.length === 0 && !layout.today)) {
    return <p className={classNames.empty}>{labels.emptyMessage}</p>;
  }

  return (
    <div
      className={[classNames.root, className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
    >
      <div className={classNames.track}>
        <span className={classNames.rail} aria-hidden="true" />

        {layout.today ? (
          <div
            className={classNames.now}
            style={{ left: `${layout.today.leftPercent}%` }}
            title={`${labels.todayMarkerTitle} · ${layout.today.dateLabel}`}
          >
            <span className={classNames.todayTag}>
              <Flag size={10} strokeWidth={2.5} aria-hidden="true" />
              {labels.todayTag}
            </span>
            <span className={classNames.flag} aria-hidden="true">
              <Flag size={14} strokeWidth={2.4} aria-hidden="true" />
            </span>
            <span className={classNames.stem} aria-hidden="true" />
            <span className={classNames.pin} aria-hidden="true" />
            <span className="delpi-ui-htimeline__sr-only">
              {labels.todayMarkerTitle} {layout.today.dateLabel}
            </span>
          </div>
        ) : null}

        <ol className={classNames.milestones}>
          {layout.events.map((point) => {
            const modifiers = [
              point.tone,
              ...(point.isCurrent ? (["current"] as const) : []),
            ];
            const itemBases = classNames.item.split(/\s+/).filter(Boolean);
            const itemClass = [
              ...itemBases,
              ...modifiers.flatMap((mod) => itemBases.map((base) => `${base}--${mod}`)),
            ].join(" ");

            return (
              <li
                key={point.id}
                className={itemClass}
                style={{ left: `${point.leftPercent}%` }}
              >
                <span className={classNames.dot} aria-hidden="true" />
                <div className={classNames.caption}>
                  <span className={classNames.label}>{point.label}</span>
                  <time className={classNames.date} dateTime={point.dateIso}>
                    {point.dateLabel}
                  </time>
                  {point.isCurrent ? (
                    <span className={classNames.currentTag}>{labels.currentTag}</span>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}

export type DashboardHorizontalTimelineProps = Omit<HorizontalTimelineProps, "classNames">;

export function createDashboardHorizontalTimeline(config: { prefix: string }) {
  const classNames = horizontalTimelineBemClasses(config.prefix);
  return function DashboardHorizontalTimeline(props: DashboardHorizontalTimelineProps) {
    return <HorizontalTimeline classNames={classNames} {...props} />;
  };
}
