import type { ReactNode } from "react";

import { delpiUiClass } from "../../utils/delpiUiClass";

export type ChartViewShellClassNames = {
  root: string;
  toolbar: string;
  toolbarPrimary: string;
  control: string;
  controlLabel: string;
  plot: string;
};

export type ChartViewShellProps = {
  /** Granularity / period controls. */
  granularity?: ReactNode;
  /** Label above granularity (empty string hides). */
  granularityLabel?: string;
  /**
   * Overlay options popover (YoY / trend) — same primary row as
   * granularity and chart type.
   */
  overlays?: ReactNode;
  /** Label above overlays (empty string hides). */
  overlaysLabel?: string;
  /** Chart type segment toggle. */
  typeToggle?: ReactNode;
  /** Label above type toggle (empty string hides). */
  typeToggleLabel?: string;
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
    control: pair(`${local}__control`, `${ui}__control`),
    controlLabel: pair(`${local}__control-label`, `${ui}__control-label`),
    plot: pair(`${local}__plot`, `${ui}__plot`),
  };
}

function ChartViewShellControl({
  label,
  classNames,
  children,
}: {
  label: string;
  classNames: Pick<ChartViewShellClassNames, "control" | "controlLabel">;
  children: ReactNode;
}) {
  const showLabel = label.trim().length > 0;
  return (
    <div className={classNames.control}>
      {showLabel ? <span className={classNames.controlLabel}>{label}</span> : null}
      {children}
    </div>
  );
}

/**
 * Dense chart toolbar: granularity + overlays + type + export on one row.
 */
export function ChartViewShell({
  granularity,
  granularityLabel = "Agrupamento",
  overlays,
  overlaysLabel = "Opções",
  typeToggle,
  typeToggleLabel = "Tipo",
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
    control: classNamesOverride?.control ?? base.control,
    controlLabel: classNamesOverride?.controlLabel ?? base.controlLabel,
    plot: classNamesOverride?.plot ?? base.plot,
  };

  const hasToolbar =
    granularity || overlays || typeToggle || exportActions || extra;

  return (
    <div className={[classNames.root, className].filter(Boolean).join(" ")}>
      {hasToolbar ? (
        <div className={classNames.toolbar}>
          <div className={classNames.toolbarPrimary}>
            {granularity ? (
              <ChartViewShellControl
                label={granularityLabel}
                classNames={classNames}
              >
                {granularity}
              </ChartViewShellControl>
            ) : null}
            {overlays ? (
              <ChartViewShellControl label={overlaysLabel} classNames={classNames}>
                {overlays}
              </ChartViewShellControl>
            ) : null}
            {typeToggle ? (
              <ChartViewShellControl label={typeToggleLabel} classNames={classNames}>
                {typeToggle}
              </ChartViewShellControl>
            ) : null}
            {extra}
            {exportActions ? (
              <div className="delpi-ui-chart-view-shell__export">{exportActions}</div>
            ) : null}
          </div>
        </div>
      ) : null}
      <div className={classNames.plot}>{children}</div>
    </div>
  );
}
