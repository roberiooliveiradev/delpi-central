import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type TimelineTone = "default" | "danger" | "warning" | "success" | "info";

/** `linear` = lista vertical; `tree` = ramifica a partir de `parentId`. */
export type TimelineLayout = "linear" | "tree";

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
  /**
   * Pai na árvore (só `layout="tree"`).
   * Ausente / null / id inexistente → raiz do tronco.
   */
  parentId?: string | null;
  /** Chave opcional do trilho (cor/estilo); ex.: `"main"`, `"alt-a"`. */
  branchKey?: string;
};

export type TimelineTreeNode = {
  item: TimelineItemModel;
  children: TimelineTreeNode[];
};

export type TimelineClassNames = {
  root: string;
  rootTree: string;
  track: string;
  trackNested: string;
  entry: string;
  entryBranch: string;
  marker: string;
  body: string;
  header: string;
  title: string;
  time: string;
  detail: string;
  meta: string;
  empty: string;
  loading: string;
};

export type TimelineProps = {
  items: TimelineItemModel[];
  emptyMessage?: string;
  loading?: boolean;
  loadingMessage?: string;
  /** Default `linear`. Com `tree`, monta floresta via `parentId`. */
  layout?: TimelineLayout;
  className?: string;
  classNames: TimelineClassNames;
  /** Prefixo BEM local — usado nos modifiers de tom do marker. */
  prefix: string;
  block?: string;
  "aria-label"?: string;
};

/**
 * Monta floresta a partir de `parentId`.
 * - Pai ausente / inexistente / self → raiz.
 * - Ciclos são cortados (nó ciclado vira raiz).
 * - Ordem dos irmãos = ordem de aparição em `items`.
 */
export function buildTimelineForest(items: TimelineItemModel[]): TimelineTreeNode[] {
  const byId = new Map<string, TimelineItemModel>();
  for (const item of items) {
    byId.set(item.id, item);
  }

  const childrenByParent = new Map<string, TimelineItemModel[]>();
  const roots: TimelineItemModel[] = [];

  for (const item of items) {
    const rawParent = item.parentId?.trim() || null;
    const parentOk = Boolean(rawParent && rawParent !== item.id && byId.has(rawParent));
    if (!parentOk) {
      roots.push(item);
      continue;
    }
    const list = childrenByParent.get(rawParent!) ?? [];
    list.push(item);
    childrenByParent.set(rawParent!, list);
  }

  const visiting = new Set<string>();
  const placed = new Set<string>();

  function buildNode(item: TimelineItemModel): TimelineTreeNode {
    if (visiting.has(item.id)) {
      return { item, children: [] };
    }
    visiting.add(item.id);
    const kids = childrenByParent.get(item.id) ?? [];
    const children: TimelineTreeNode[] = [];
    for (const child of kids) {
      if (visiting.has(child.id)) continue;
      children.push(buildNode(child));
    }
    visiting.delete(item.id);
    placed.add(item.id);
    return { item, children };
  }

  const forest = roots.map(buildNode);

  for (const item of items) {
    if (!placed.has(item.id)) {
      forest.push(buildNode(item));
    }
  }

  return forest;
}

export function timelineBemClasses(prefix: string, block = "timeline"): TimelineClassNames {
  const root = `${prefix}-${block}`;
  const ui = "delpi-ui-timeline";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);

  return {
    root: pair(root, ui),
    rootTree: pair(`${root}--tree`, `${ui}--tree`),
    track: pair(`${root}__track`, `${ui}__track`),
    trackNested: pair(`${root}__track--nested`, `${ui}__track--nested`),
    entry: pair(`${root}__entry`, `${ui}__entry`),
    entryBranch: pair(`${root}__entry--branch`, `${ui}__entry--branch`),
    marker: pair(`${root}__marker`, `${ui}__marker`),
    body: pair(`${root}__body`, `${ui}__body`),
    header: pair(`${root}__header`, `${ui}__header`),
    title: pair(`${root}__title`, `${ui}__title`),
    time: pair(`${root}__time`, `${ui}__time`),
    detail: pair(`${root}__detail`, `${ui}__detail`),
    meta: pair(`${root}__meta`, `${ui}__meta`),
    empty: pair(`${root}__empty`, `${ui}__empty`),
    loading: pair(`${root}__loading`, `${ui}__loading`),
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

function TimelineEntryContent({
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
    <>
      <span className={markerClass} aria-hidden="true">
        {item.marker ?? null}
      </span>
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
          <div className={classNames.detail}>{item.detail}</div>
        ) : null}
        {item.meta != null && item.meta !== "" ? (
          <div className={classNames.meta}>{item.meta}</div>
        ) : null}
      </div>
    </>
  );
}

function TimelineTreeList({
  nodes,
  classNames,
  prefix,
  block,
  nested,
  ariaLabel,
}: {
  nodes: TimelineTreeNode[];
  classNames: TimelineClassNames;
  prefix: string;
  block: string;
  nested: boolean;
  ariaLabel?: string;
}) {
  const trackClass = [classNames.track, nested ? classNames.trackNested : ""]
    .filter(Boolean)
    .join(" ");

  return (
    <ol className={trackClass} aria-label={nested ? undefined : ariaLabel}>
      {nodes.map((node) => {
        const entryClass = [
          classNames.entry,
          nested ? classNames.entryBranch : "",
        ]
          .filter(Boolean)
          .join(" ");
        const branchKey = node.item.branchKey?.trim();

        return (
          <li
            key={node.item.id}
            className={entryClass}
            data-branch-key={branchKey || undefined}
          >
            <TimelineEntryContent
              item={node.item}
              classNames={classNames}
              prefix={prefix}
              block={block}
            />
            {node.children.length > 0 ? (
              <TimelineTreeList
                nodes={node.children}
                classNames={classNames}
                prefix={prefix}
                block={block}
                nested
              />
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

export function Timeline({
  items,
  emptyMessage = "Nenhum evento.",
  loading = false,
  loadingMessage = "Carregando…",
  layout = "linear",
  className,
  classNames,
  prefix,
  block = "timeline",
  "aria-label": ariaLabel = "Linha do tempo",
}: TimelineProps) {
  const rootClass = [
    classNames.root,
    layout === "tree" ? classNames.rootTree : "",
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

  if (layout === "tree") {
    const forest = buildTimelineForest(items);
    return (
      <div className={rootClass}>
        <TimelineTreeList
          nodes={forest}
          classNames={classNames}
          prefix={prefix}
          block={block}
          nested={false}
          ariaLabel={ariaLabel}
        />
      </div>
    );
  }

  return (
    <div className={rootClass}>
      <ol className={classNames.track} aria-label={ariaLabel}>
        {items.map((item) => (
          <li
            key={item.id}
            className={classNames.entry}
            data-branch-key={item.branchKey?.trim() || undefined}
          >
            <TimelineEntryContent
              item={item}
              classNames={classNames}
              prefix={prefix}
              block={block}
            />
          </li>
        ))}
      </ol>
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
