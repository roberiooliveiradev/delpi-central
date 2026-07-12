import type { ReactNode } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";

export type ChartFrameProps = {
  viewW: number;
  viewH: number;
  ariaLabel: string;
  children: ReactNode;
};

export function ChartFrame({ viewW, viewH, ariaLabel, children }: ChartFrameProps) {
  const cn = useSeriesChartClasses();
  return (
    <svg
      viewBox={`0 0 ${viewW} ${viewH}`}
      className={cn.svg}
      preserveAspectRatio="xMidYMid meet"
      role="img"
      aria-label={ariaLabel}
      overflow="hidden"
      style={{ overflow: "hidden" }}
    >
      {children}
    </svg>
  );
}
