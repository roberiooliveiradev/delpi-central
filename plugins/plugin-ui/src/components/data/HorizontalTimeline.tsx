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
  axis: string;
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
    axis: delpiUiClass(`${block}__axis`, "delpi-ui-htimeline__axis"),
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
  edgePadPercent = 8,
): number {
  const ms = parseIsoDay(dateIso);
  if (ms == null) return 50;
  const span = Math.max(rangeEndMs - rangeStartMs, 1);
  const raw = ((ms - rangeStartMs) / span) * 100;
  const padded = edgePadPercent + (raw / 100) * (100 - edgePadPercent * 2);
  return Math.min(100 - edgePadPercent, Math.max(edgePadPercent, padded));
}

export type HorizontalTimelineCluster = {
  id: string;
  dateIso: string;
  dateLabel: string;
  leftPercent: number;
  isCurrent: boolean;
  /** Tom do destaque (prioridade: current → danger → warning → success → info → neutral). */
  tone: HorizontalTimelineTone;
  entries: Array<{ id: string; label: string; tone: HorizontalTimelineTone }>;
};

const TONE_PRIORITY: Record<HorizontalTimelineTone, number> = {
  danger: 5,
  warning: 4,
  success: 3,
  info: 2,
  neutral: 1,
};

function pickClusterTone(
  entries: HorizontalTimelinePoint[],
  isCurrent: boolean,
): HorizontalTimelineTone {
  if (isCurrent) {
    const current = entries.find((e) => e.isCurrent);
    if (current) return current.tone;
  }
  return entries.reduce<HorizontalTimelineTone>(
    (best, entry) =>
      TONE_PRIORITY[entry.tone] > TONE_PRIORITY[best] ? entry.tone : best,
    "neutral",
  );
}

/**
 * Agrupa eventos do mesmo dia (um ponto no trilho, legendas empilhadas)
 * e distribui os grupos de forma uniforme — evita sobreposição de captions.
 * «Agora» usa eixo cronológico alinhado aos grupos (mesmo dia = mesmo X).
 */
export function layoutHorizontalTimeline(
  points: HorizontalTimelinePoint[],
  edgePad = 8,
): {
  clusters: HorizontalTimelineCluster[];
  today: { dateIso: string; dateLabel: string; leftPercent: number } | null;
} {
  const events = points.filter((p) => p.kind !== "today");
  const todayPoint = points.find((p) => p.kind === "today") ?? null;

  const byDay = new Map<string, HorizontalTimelinePoint[]>();
  for (const event of events) {
    const day = event.dateIso.trim();
    if (!day) continue;
    const list = byDay.get(day) ?? [];
    list.push(event);
    byDay.set(day, list);
  }

  const days = [...byDay.keys()].sort((a, b) => a.localeCompare(b));
  const n = days.length;
  const clusters: HorizontalTimelineCluster[] = days.map((dateIso, index) => {
    const entries = byDay.get(dateIso) ?? [];
    const isCurrent = entries.some((e) => Boolean(e.isCurrent));
    const leftPercent =
      n <= 1 ? 50 : edgePad + (index / (n - 1)) * (100 - edgePad * 2);
    return {
      id: `day-${dateIso}`,
      dateIso,
      dateLabel: entries[0]?.dateLabel ?? dateIso,
      leftPercent,
      isCurrent,
      tone: pickClusterTone(entries, isCurrent),
      entries: entries.map((e) => ({
        id: e.id,
        label: e.label,
        tone: e.tone,
      })),
    };
  });

  if (!todayPoint) {
    return { clusters, today: null };
  }

  const todayMs = parseIsoDay(todayPoint.dateIso);
  let leftPercent = 50;

  if (clusters.length === 0) {
    leftPercent = 50;
  } else if (clusters.length === 1) {
    leftPercent = clusters[0].leftPercent;
  } else {
    const sameDay = clusters.find((c) => c.dateIso === todayPoint.dateIso);
    if (sameDay) {
      leftPercent = sameDay.leftPercent;
    } else if (todayMs == null) {
      leftPercent = clusters[clusters.length - 1].leftPercent;
    } else {
      const firstMs = parseIsoDay(clusters[0].dateIso) ?? todayMs;
      const lastMs = parseIsoDay(clusters[clusters.length - 1].dateIso) ?? todayMs;
      if (todayMs <= firstMs) {
        leftPercent = clusters[0].leftPercent;
      } else if (todayMs >= lastMs) {
        leftPercent = clusters[clusters.length - 1].leftPercent;
      } else {
        let lo = 0;
        for (let i = 0; i < clusters.length - 1; i += 1) {
          const a = parseIsoDay(clusters[i].dateIso) ?? 0;
          const b = parseIsoDay(clusters[i + 1].dateIso) ?? 0;
          if (todayMs >= a && todayMs <= b) {
            lo = i;
            break;
          }
        }
        const aMs = parseIsoDay(clusters[lo].dateIso) ?? todayMs;
        const bMs = parseIsoDay(clusters[lo + 1].dateIso) ?? todayMs;
        const t = bMs === aMs ? 0 : (todayMs - aMs) / (bMs - aMs);
        leftPercent =
          clusters[lo].leftPercent +
          t * (clusters[lo + 1].leftPercent - clusters[lo].leftPercent);
      }
    }
  }

  return {
    clusters,
    today: {
      dateIso: todayPoint.dateIso,
      dateLabel: todayPoint.dateLabel,
      leftPercent,
    },
  };
}

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

  const layout = useMemo(() => layoutHorizontalTimeline(points), [points]);

  if (points.length === 0 || (layout.clusters.length === 0 && !layout.today)) {
    return <p className={classNames.empty}>{labels.emptyMessage}</p>;
  }

  const trackStyle = {
    // Mais espaço abaixo quando um dia tem várias legendas empilhadas.
    ["--delpi-ui-htimeline-caption-rows" as string]: String(
      Math.max(1, ...layout.clusters.map((c) => c.entries.length), 1),
    ),
  };

  return (
    <div
      className={[classNames.root, className].filter(Boolean).join(" ")}
      role="group"
      aria-label={ariaLabel}
      style={trackStyle}
    >
      <div className={classNames.track}>
        <div className={classNames.axis}>
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
            {layout.clusters.map((cluster) => {
              const modifiers = [
                cluster.tone,
                ...(cluster.isCurrent ? (["current"] as const) : []),
                ...(cluster.entries.length > 1 ? (["stacked"] as const) : []),
              ];
              const itemBases = classNames.item.split(/\s+/).filter(Boolean);
              const itemClass = [
                ...itemBases,
                ...modifiers.flatMap((mod) =>
                  itemBases.map((base) => `${base}--${mod}`),
                ),
              ].join(" ");

              return (
                <li
                  key={cluster.id}
                  className={itemClass}
                  style={{ left: `${cluster.leftPercent}%` }}
                >
                  <span className={classNames.dot} aria-hidden="true" />
                  <div className={classNames.caption}>
                    {cluster.entries.map((entry) => (
                      <span key={entry.id} className={classNames.label}>
                        {entry.label}
                      </span>
                    ))}
                    <time className={classNames.date} dateTime={cluster.dateIso}>
                      {cluster.dateLabel}
                    </time>
                    {cluster.isCurrent ? (
                      <span className={classNames.currentTag}>{labels.currentTag}</span>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ol>
        </div>
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
