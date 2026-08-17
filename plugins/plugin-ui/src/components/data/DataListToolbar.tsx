import type { CSSProperties, ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type DataListToolbarClassNames = {
  root: string;
  leading: string;
  layout: string;
  hint: string;
  actions: string;
};

export type DataListToolbarProps = {
  leading?: ReactNode;
  hint?: ReactNode;
  actions?: ReactNode;
  className?: string;
  style?: CSSProperties;
  classNames: DataListToolbarClassNames;
};

export function dataListToolbarBemClasses(prefix: string): DataListToolbarClassNames {
  const base = `${prefix}-data-list-toolbar`;
  const ui = "delpi-ui-data-list-toolbar";
  const pair = (local: string, canonical: string) => delpiUiClass(local, canonical);
  return {
    root: pair(base, ui),
    leading: pair(`${base}__leading`, `${ui}__leading`),
    layout: pair(`${base}__layout`, `${ui}__layout`),
    hint: pair(`${base}__hint`, `${ui}__hint`),
    actions: pair(`${base}__actions`, `${ui}__actions`),
  };
}

export function DataListToolbar({
  leading,
  hint,
  actions,
  className,
  style,
  classNames,
}: DataListToolbarProps) {
  const rootClass = [classNames.root, className].filter(Boolean).join(" ");

  return (
    <div className={rootClass} style={style}>
      {leading != null || hint != null ? (
        <div className={classNames.leading}>
          {leading != null ? <div className={classNames.layout}>{leading}</div> : null}
          {hint != null ? <div className={classNames.hint}>{hint}</div> : null}
        </div>
      ) : null}
      {actions != null ? <div className={classNames.actions}>{actions}</div> : null}
    </div>
  );
}

export type DashboardDataListToolbarProps = Omit<DataListToolbarProps, "classNames">;

export function createDashboardDataListToolbar(config: { prefix: string }) {
  const classNames = dataListToolbarBemClasses(config.prefix);
  return function DashboardDataListToolbar(props: DashboardDataListToolbarProps) {
    return <DataListToolbar classNames={classNames} {...props} />;
  };
}
