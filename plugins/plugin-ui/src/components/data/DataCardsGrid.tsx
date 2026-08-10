import type { CSSProperties, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type DataCardsGridClassNames = {
  root: string;
  empty: string;
};

export type DataCardsGridProps = {
  children?: ReactNode;
  empty?: ReactNode;
  ariaLabel?: string;
  className?: string;
  style?: CSSProperties;
  classNames: DataCardsGridClassNames;
};

export function dataCardsGridBemClasses(prefix: string): DataCardsGridClassNames {
  const base = `${prefix}-data-cards-grid`;
  const ui = "delpi-ui-data-cards-grid";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    empty: pair(`${base}__empty`, `${ui}__empty`),
  };
}

export function DataCardsGrid({
  children,
  empty,
  ariaLabel,
  className,
  style,
  classNames,
}: DataCardsGridProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");
  const showEmpty = empty != null;

  return (
    <div className={rootClass} style={style} aria-label={ariaLabel}>
      {showEmpty ? (
        typeof empty === "string" ? (
          <p className={classNames.empty}>{empty}</p>
        ) : (
          empty
        )
      ) : (
        children
      )}
    </div>
  );
}

export type DashboardDataCardsGridProps = Omit<DataCardsGridProps, "classNames">;

export function createDashboardDataCardsGrid(config: { prefix: string }) {
  const classNames = dataCardsGridBemClasses(config.prefix);
  return function DashboardDataCardsGrid(props: DashboardDataCardsGridProps) {
    return <DataCardsGrid classNames={classNames} {...props} />;
  };
}

export type DataCardsSortBarClassNames = {
  root: string;
  direction: string;
};

export type DataCardsSortBarProps = {
  sortField?: ReactNode;
  direction?: ReactNode;
  children?: ReactNode;
  className?: string;
  style?: CSSProperties;
  classNames: DataCardsSortBarClassNames;
};

export function dataCardsSortBarBemClasses(prefix: string): DataCardsSortBarClassNames {
  const base = `${prefix}-data-cards-sort-bar`;
  const ui = "delpi-ui-data-cards-sort-bar";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    direction: pair(`${base}__dir`, `${ui}__dir`),
  };
}

export function DataCardsSortBar({
  sortField,
  direction,
  children,
  className,
  style,
  classNames,
}: DataCardsSortBarProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  if (children != null) {
    return (
      <div className={rootClass} style={style}>
        {children}
      </div>
    );
  }

  return (
    <div className={rootClass} style={style}>
      {sortField}
      {direction != null ? <div className={classNames.direction}>{direction}</div> : null}
    </div>
  );
}

export type DashboardDataCardsSortBarProps = Omit<DataCardsSortBarProps, "classNames">;

export function createDashboardDataCardsSortBar(config: { prefix: string }) {
  const classNames = dataCardsSortBarBemClasses(config.prefix);
  return function DashboardDataCardsSortBar(props: DashboardDataCardsSortBarProps) {
    return <DataCardsSortBar classNames={classNames} {...props} />;
  };
}
