import type { CSSProperties, PointerEventHandler, ReactNode } from "react";

import { useSeriesChartClasses } from "../seriesChartClasses";

export type ChartContainerProps = {
  className?: string;
  empty?: boolean;
  emptyMessage?: string;
  style?: CSSProperties;
  children?: ReactNode;
  onPointerDown?: PointerEventHandler<HTMLDivElement>;
  "data-chart-part"?: string;
  "aria-selected"?: boolean;
};

export function ChartContainer({
  className,
  empty,
  emptyMessage = "Sem série",
  style,
  children,
  onPointerDown,
  ...domProps
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
    <div
      className={[cn.root, className].filter(Boolean).join(" ")}
      style={style}
      onPointerDown={onPointerDown}
      {...domProps}
    >
      {children}
    </div>
  );
}
