import type { CSSProperties, ReactNode } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";

export type ChartContainerProps = {
  className?: string;
  empty?: boolean;
  emptyMessage?: string;
  style?: CSSProperties;
  children?: ReactNode;
};

export function ChartContainer({
  className,
  empty,
  emptyMessage = "Sem série",
  style,
  children,
}: ChartContainerProps) {
  const cn = useSeriesChartClasses();

  if (empty) {
    return (
      <div className={[cn.rootEmpty, className].filter(Boolean).join(" ")} style={style}>
        {emptyMessage}
      </div>
    );
  }

  return (
    <div className={[cn.root, className].filter(Boolean).join(" ")} style={style}>
      {children}
    </div>
  );
}
