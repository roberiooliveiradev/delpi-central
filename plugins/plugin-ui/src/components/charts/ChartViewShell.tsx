import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type ChartViewShellClassNames = {
  root: string;
  toolbar: string;
  toolbarPrimary: string;
  toolbarOverlays: string;
  plot: string;
};

export type ChartViewShellProps = {
  /** Granularity / period controls. */
  granularity?: ReactNode;
  /** Chart type segment toggle. */
  typeToggle?: ReactNode;
  /** Compact overlay checkboxes (YoY, trend). */
  overlays?: ReactNode;
  /** Export buttons (Excel / CSV / PDF). */
  exportActions?: ReactNode;
  /** Extra trailing controls. */
  extra?: ReactNode;
  children: ReactNode;
  className?: string;
  prefix?: string;
  classNames?: Partial<ChartViewShellClassNames>;
};

export function chartViewShellBemClasses(prefix: string): ChartViewShellClassNames {
  const local = `${prefix}-chart-view-shell`;
  const ui = "delpi-ui-chart-view-shell";
  const pair = (a: string, b: string) => delpiUiClass(a, b);
  return {
    root: pair(local, ui),
    toolbar: pair(`${local}__toolbar`, `${ui}__toolbar`),
    toolbarPrimary: pair(`${local}__toolbar-primary`, `${ui}__toolbar-primary`),
    toolbarOverlays: pair(`${local}__toolbar-overlays`, `${ui}__toolbar-overlays`),
    plot: pair(`${local}__plot`, `${ui}__plot`),
  };
}

/**
 * Dense chart toolbar shell: granularity + type + overlays + export above the plot.
 */
export function ChartViewShell({
  granularity,
  typeToggle,
  overlays,
  exportActions,
  extra,
  children,
  className,
  prefix = "ds",
  classNames: classNamesOverride,
}: ChartViewShellProps) {
  const base = chartViewShellBemClasses(prefix);
  const classNames: ChartViewShellClassNames = {
    root: classNamesOverride?.root ?? base.root,
    toolbar: classNamesOverride?.toolbar ?? base.toolbar,
    toolbarPrimary: classNamesOverride?.toolbarPrimary ?? base.toolbarPrimary,
    toolbarOverlays: classNamesOverride?.toolbarOverlays ?? base.toolbarOverlays,
    plot: classNamesOverride?.plot ?? base.plot,
  };

  const hasToolbar =
    granularity || typeToggle || overlays || exportActions || extra;

  return (
    <div className={[classNames.root, className].filter(Boolean).join(" ")}>
      {hasToolbar ? (
        <div className={classNames.toolbar}>
          <div className={classNames.toolbarPrimary}>
            {granularity}
            {typeToggle}
            {extra}
            {exportActions ? (
              <div className="delpi-ui-chart-view-shell__export">{exportActions}</div>
            ) : null}
          </div>
          {overlays ? (
            <div className={classNames.toolbarOverlays}>{overlays}</div>
          ) : null}
        </div>
      ) : null}
      <div className={classNames.plot}>{children}</div>
    </div>
  );
}
