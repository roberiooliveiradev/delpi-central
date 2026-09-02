import { useMemo, type ReactNode } from "react";

import {
  ChartCard,
  chartCardBemClasses,
  ComparativeAreaChart,
  useDelpiDarkMode,
} from "@delpi/plugin-ui/index";

import type { ChartPoint } from "../../utils/detailDisplay";
import {
  buildPpReadingsChartSeries,
  formatPpReadingsChartValue,
  readingsToComparativeData,
  resolvePpReadingsChartHeight,
  resolvePpReadingsChartYAxisWidth,
  type PpReadingsChartVariant,
} from "./ppChartConfig";

export type { PpReadingsChartVariant } from "./ppChartConfig";
export {
  buildPpReadingsChartSeries,
  formatPpReadingsChartValue,
  readingsToComparativeData,
  readingsToSeriesPoints,
} from "./ppChartConfig";

const PREFIX = "pp";
const CHART_CARD_CLASSES = chartCardBemClasses(PREFIX, { headerLayout: "titleRow" });

type PpReadingsAreaChartProps = {
  points: ChartPoint[];
  height?: number;
  emptyMessage?: string;
  variant?: PpReadingsChartVariant;
};

/** Série temporal interativa — ComparativeAreaChart (Recharts) com tooltip e tema claro/escuro. */
export function PpReadingsAreaChart({
  points,
  height,
  emptyMessage = "Sem leituras no período.",
  variant = "detail",
}: PpReadingsAreaChartProps) {
  const isDark = useDelpiDarkMode();
  const resolvedHeight = resolvePpReadingsChartHeight(variant, height);
  const series = useMemo(() => buildPpReadingsChartSeries(isDark), [isDark]);
  const data = useMemo(() => readingsToComparativeData(points), [points]);

  if (points.length === 0) {
    return <p className="pp-chart-empty">{emptyMessage}</p>;
  }

  return (
    <div className="pp-readings-chart" style={{ minHeight: resolvedHeight }}>
      <ComparativeAreaChart
        prefix={PREFIX}
        className="pp-readings-chart__series"
        data={data}
        series={series}
        height={resolvedHeight}
        yAxisWidth={resolvePpReadingsChartYAxisWidth(variant)}
        valueFormatter={formatPpReadingsChartValue}
        emptyMessage={emptyMessage}
        smooth
      />
    </div>
  );
}

type PpChartCardProps = {
  title: string;
  hint?: string;
  titleHint?: string;
  children: ReactNode;
  headerActions?: ReactNode;
};

/** Shell de gráfico — `ChartCard` do kit com BEM `pp`. */
export function PpChartCard({ title, hint, titleHint, children, headerActions }: PpChartCardProps) {
  return (
    <ChartCard
      title={title}
      hint={hint}
      titleHint={titleHint}
      headerActions={headerActions}
      classNames={CHART_CARD_CLASSES}
    >
      {children}
    </ChartCard>
  );
}
