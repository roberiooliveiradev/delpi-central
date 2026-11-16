import type { ReactNode } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";

export type ChartFrameProps = {
  viewW: number;
  viewH: number;
  ariaLabel: string;
  children: ReactNode;
  /**
   * When bars/points are keyboard-focusable (onPointSelect), use role=group
   * so nested role=button is valid (same pattern as DistributionDonut).
   */
  interactivePoints?: boolean;
};

export function ChartFrame({
  viewW,
  viewH,
  ariaLabel,
  children,
  interactivePoints = false,
}: ChartFrameProps) {
  const cn = useSeriesChartClasses();
  return (
    <svg
      viewBox={`0 0 ${viewW} ${viewH}`}
      className={cn.svg}
      preserveAspectRatio="xMidYMid meet"
      role={interactivePoints ? "group" : "img"}
      aria-label={ariaLabel}
      overflow="hidden"
      style={{ overflow: "hidden" }}
    >
      {children}
    </svg>
  );
}
