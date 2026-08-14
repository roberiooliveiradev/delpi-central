import type { CSSProperties, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type KanbanBoardColumn = {
  id: string;
  title: ReactNode;
  /** Optional count shown in the column header. */
  count?: number | string;
  /** Optional secondary metric (e.g. currency sum). */
  summary?: ReactNode;
  /** Cards for this column (already rendered). */
  children?: ReactNode;
  /** Shown when the column has no cards. */
  empty?: ReactNode;
};

export type KanbanBoardClassNames = {
  root: string;
  column: string;
  header: string;
  title: string;
  meta: string;
  body: string;
  empty: string;
  card: string;
};

export type KanbanBoardProps = {
  columns: KanbanBoardColumn[];
  /** Optional aria label for the board region. */
  ariaLabel?: string;
  className?: string;
  style?: CSSProperties;
  classNames: KanbanBoardClassNames;
};

export function kanbanBoardBemClasses(prefix: string): KanbanBoardClassNames {
  const base = `${prefix}-kanban-board`;
  const ui = "delpi-ui-kanban-board";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    column: pair(`${base}__column`, `${ui}__column`),
    header: pair(`${base}__header`, `${ui}__header`),
    title: pair(`${base}__title`, `${ui}__title`),
    meta: pair(`${base}__meta`, `${ui}__meta`),
    body: pair(`${base}__body`, `${ui}__body`),
    empty: pair(`${base}__empty`, `${ui}__empty`),
    card: pair(`${base}__card`, `${ui}__card`),
  };
}

/**
 * Read-only Kanban board: columns + card slots. No drag-and-drop.
 * Domain-free — titles/labels come from the consumer.
 */
export function KanbanBoard({
  columns,
  ariaLabel,
  className,
  style,
  classNames,
}: KanbanBoardProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div
      className={rootClass}
      style={style}
      role="region"
      aria-label={ariaLabel}
    >
      {columns.map((column) => {
        const hasCards = column.children != null && column.children !== false;
        return (
          <section
            key={column.id}
            className={classNames.column}
            data-kanban-column={column.id}
            aria-labelledby={`kanban-col-${column.id}`}
          >
            <header className={classNames.header}>
              <h3 className={classNames.title} id={`kanban-col-${column.id}`}>
                {column.title}
              </h3>
              <div className={classNames.meta}>
                {column.count != null ? <span>{column.count}</span> : null}
                {column.summary != null ? <span>{column.summary}</span> : null}
              </div>
            </header>
            <div className={classNames.body}>
              {hasCards ? (
                column.children
              ) : column.empty != null ? (
                typeof column.empty === "string" ? (
                  <p className={classNames.empty}>{column.empty}</p>
                ) : (
                  column.empty
                )
              ) : null}
            </div>
          </section>
        );
      })}
    </div>
  );
}

export type DashboardKanbanBoardProps = Omit<KanbanBoardProps, "classNames">;

export function createDashboardKanbanBoard(config: { prefix: string }) {
  const classNames = kanbanBoardBemClasses(config.prefix);
  return function DashboardKanbanBoard(props: DashboardKanbanBoardProps) {
    return <KanbanBoard classNames={classNames} {...props} />;
  };
}
