import { useEffect, useMemo, useState, type ReactNode } from "react";

import {
  AreaSeriesChart,
  ChartCard,
  chartCardBemClasses,
  type SeriesChartTheme,
} from "@delpi/plugin-ui/index";

import type { ChartPoint } from "../../utils/detailDisplay";
import {
  buildPpReadingsChartOptions,
  readingsToSeriesPoints,
  type PpReadingsChartVariant,
} from "./ppChartConfig";

export type { PpReadingsChartVariant } from "./ppChartConfig";
export { buildPpReadingsChartOptions, readingsToSeriesPoints } from "./ppChartConfig";

const PREFIX = "pp";
const CHART_CARD_CLASSES = chartCardBemClasses(PREFIX, { headerLayout: "titleRow" });

function resolveHostChartTheme(): SeriesChartTheme {
  if (typeof document === "undefined") return "light";
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function usePpChartTheme(): SeriesChartTheme {
  const [theme, setTheme] = useState<SeriesChartTheme>(() => resolveHostChartTheme());

  useEffect(() => {
    const syncTheme = () => setTheme(resolveHostChartTheme());
    syncTheme();
    const observer = new MutationObserver(syncTheme);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });
    return () => observer.disconnect();
  }, []);

  return theme;
}

type PpReadingsAreaChartProps = {
  points: ChartPoint[];
  height?: number;
  emptyMessage?: string;
  variant?: PpReadingsChartVariant;
};

/** Série temporal de leituras — `AreaSeriesChart` do kit com tema do portal. */
export function PpReadingsAreaChart({
  points,
  height = 220,
  emptyMessage = "Sem leituras no período.",
  variant = "detail",
}: PpReadingsAreaChartProps) {
  const theme = usePpChartTheme();
  const options = useMemo(
    () => buildPpReadingsChartOptions(variant, theme),
    [theme, variant],
  );

  if (points.length === 0) {
    return <p className="pp-chart-empty">{emptyMessage}</p>;
  }

  return (
    <div className="pp-readings-chart" style={{ minHeight: height }}>
      <AreaSeriesChart
        className="pp-readings-chart__series"
        points={readingsToSeriesPoints(points)}
        options={options}
        emptyMessage={emptyMessage}
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
