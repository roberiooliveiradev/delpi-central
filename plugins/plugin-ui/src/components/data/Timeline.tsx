import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type TimelineTone = "default" | "danger" | "warning" | "success" | "info";

export type TimelineVariant = "feed" | "table";

export type TimelineItemModel = {
  id: string;
  title: ReactNode;
  /** Valor ISO/raw para o atributo `dateTime` do `<time>`. */
  occurredAt?: string | null;
  /** Texto exibido à direita do título (ex.: data formatada). */
  timeLabel?: ReactNode;
  detail?: ReactNode;
  meta?: ReactNode;
  marker?: ReactNode;
  tone?: TimelineTone;
};

export type TimelineColumnLabels = {
  time?: string;
  title?: string;
  detail?: string;
  meta?: string;
};

export type TimelineClassNames = {
  root: string;
  rootTable: string;
  track: string;
  entry: string;
  marker: string;
  body: string;
  header: string;
  title: string;
  time: string;
  detail: string;
  meta: string;
  empty: string;
  loading: string;
  tableWrap: string;
  table: string;
  markerCell: string;
};

export type TimelineProps = {
  items: TimelineItemModel[];
  emptyMessage?: string;
  loading?: boolean;
  loadingMessage?: string;
  /** `feed` = cartões empilhados; `table` = grade tabular com trilho. */
  variant?: TimelineVariant;
  columnLabels?: TimelineColumnLabels;
  className?: string;
  classNames: TimelineClassNames;
  /** Prefixo BEM local — usado nos modifiers de tom do marker. */
  prefix: string;
  block?: string;
  "aria-label"?: string;
};

const DEFAULT_COLUMN_LABELS: Required<TimelineColumnLabels> = {
  time: "Quando",
  title: "Ação",
  detail: "Detalhe",
  meta: "Usuário",
};

export function timelineBemClasses(prefix: string, block = "timeline"): TimelineClassNames {
  const root = `${prefix}-${block}`;
  const ui = "delpi-ui-timeline";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(root, ui),
    rootTable: pair(`${root}--table`, `${ui}--table`),
    track: pair(`${root}__track`, `${ui}__track`),
    entry: pair(`${root}__entry`, `${ui}__entry`),
    marker: pair(`${root}__marker`, `${ui}__marker`),
    body: pair(`${root}__body`, `${ui}__body`),
    header: pair(`${root}__header`, `${ui}__header`),
    title: pair(`${root}__title`, `${ui}__title`),
    time: pair(`${root}__time`, `${ui}__time`),
    detail: pair(`${root}__detail`, `${ui}__detail`),
    meta: pair(`${root}__meta`, `${ui}__meta`),
    empty: pair(`${root}__empty`, `${ui}__empty`),
    loading: pair(`${root}__loading`, `${ui}__loading`),
    tableWrap: pair(`${root}__table-wrap`, `${ui}__table-wrap`),
    table: pair(`${root}__table`, `${ui}__table`),
    markerCell: pair(`${root}__marker-cell`, `${ui}__marker-cell`),
  };
}

export function timelineMarkerToneClass(
  prefix: string,
  tone: TimelineTone,
  block = "timeline",
): string {
  if (tone === "default") return "";
  return delpiUiClass(`${prefix}-${block}__marker--${tone}`, `delpi-ui-timeline__marker--${tone}`);
}

function TimelineMarker({
  item,
  classNames,
  prefix,
  block,
}: {
  item: TimelineItemModel;
  classNames: TimelineClassNames;
  prefix: string;
  block: string;
}) {
  const tone = item.tone ?? "default";
  const markerClass = [classNames.marker, timelineMarkerToneClass(prefix, tone, block)]
    .filter(Boolean)
    .join(" ");

  return (
    <span className={markerClass} aria-hidden="true">
      {item.marker ?? null}
    </span>
  );
}

function TimelineFeed({
  items,
  classNames,
  prefix,
  block,
  ariaLabel,
}: {
  items: TimelineItemModel[];
  classNames: TimelineClassNames;
  prefix: string;
  block: string;
  ariaLabel: string;
}) {
  return (
    <ol className={classNames.track} aria-label={ariaLabel}>
      {items.map((item) => (
        <li key={item.id} className={classNames.entry}>
          <TimelineMarker item={item} classNames={classNames} prefix={prefix} block={block} />
          <div className={classNames.body}>
            <div className={classNames.header}>
              <strong className={classNames.title}>{item.title}</strong>
              {item.timeLabel != null || item.occurredAt ? (
                <time className={classNames.time} dateTime={item.occurredAt ?? undefined}>
                  {item.timeLabel ?? item.occurredAt}
                </time>
              ) : null}
            </div>
            {item.detail != null && item.detail !== "" ? (
              <p className={classNames.detail}>{item.detail}</p>
            ) : null}
            {item.meta != null && item.meta !== "" ? (
              <p className={classNames.meta}>{item.meta}</p>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}

function TimelineTable({
  items,
  classNames,
  prefix,
  block,
  ariaLabel,
  columnLabels,
}: {
  items: TimelineItemModel[];
  classNames: TimelineClassNames;
  prefix: string;
  block: string;
  ariaLabel: string;
  columnLabels: Required<TimelineColumnLabels>;
}) {
  return (
    <div className={classNames.tableWrap}>
      <table className={classNames.table} aria-label={ariaLabel}>
        <thead>
          <tr>
            <th scope="col" className={classNames.markerCell}>
              <span className="delpi-ui-sr-only">Status</span>
            </th>
            <th scope="col">{columnLabels.time}</th>
            <th scope="col">{columnLabels.title}</th>
            <th scope="col">{columnLabels.detail}</th>
            <th scope="col">{columnLabels.meta}</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className={classNames.entry}>
              <td className={classNames.markerCell}>
                <TimelineMarker item={item} classNames={classNames} prefix={prefix} block={block} />
              </td>
              <td className={classNames.time}>
                {item.timeLabel != null || item.occurredAt ? (
                  <time dateTime={item.occurredAt ?? undefined}>
                    {item.timeLabel ?? item.occurredAt}
                  </time>
                ) : (
                  "—"
                )}
              </td>
              <td className={classNames.title}>{item.title}</td>
              <td className={classNames.detail}>
                {item.detail != null && item.detail !== "" ? item.detail : "—"}
              </td>
              <td className={classNames.meta}>
                {item.meta != null && item.meta !== "" ? item.meta : "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Timeline({
  items,
  emptyMessage = "Nenhum evento.",
  loading = false,
  loadingMessage = "Carregando…",
  variant = "feed",
  columnLabels,
  className,
  classNames,
  prefix,
  block = "timeline",
  "aria-label": ariaLabel = "Linha do tempo",
}: TimelineProps) {
  const labels = { ...DEFAULT_COLUMN_LABELS, ...columnLabels };
  const rootClass = [
    classNames.root,
    variant === "table" ? classNames.rootTable : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  if (loading && items.length === 0) {
    return (
      <div className={rootClass} aria-busy="true" aria-live="polite">
        <p className={classNames.loading}>{loadingMessage}</p>
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className={rootClass}>
        <p className={classNames.empty}>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className={rootClass}>
      {variant === "table" ? (
        <TimelineTable
          items={items}
          classNames={classNames}
          prefix={prefix}
          block={block}
          ariaLabel={ariaLabel}
          columnLabels={labels}
        />
      ) : (
        <TimelineFeed
          items={items}
          classNames={classNames}
          prefix={prefix}
          block={block}
          ariaLabel={ariaLabel}
        />
      )}
    </div>
  );
}

export type DashboardTimelineProps = Omit<TimelineProps, "classNames" | "prefix" | "block">;

export function createTimeline(config: { prefix: string; block?: string }) {
  const block = config.block ?? "timeline";
  const classNames = timelineBemClasses(config.prefix, block);

  return function DashboardTimeline(props: DashboardTimelineProps) {
    return <Timeline classNames={classNames} prefix={config.prefix} block={block} {...props} />;
  };
}
