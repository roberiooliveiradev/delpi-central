/** Lê tokens --mdc-* do :root (portal + plugin). */

export function readMdcCssVar(name: string, fallback = ""): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();

  return value || fallback;
}

export function readMdcChartSeries(count = 10): string[] {
  const colors: string[] = [];

  for (let index = 1; index <= count; index += 1) {
    colors.push(readMdcCssVar(`--mdc-chart-series-${index}`, readMdcCssVar("--mdc-primary")));
  }

  return colors;
}

export function readMdcChartTheme(isDark: boolean) {
  void isDark;

  return {
    gridColor: readMdcCssVar("--mdc-chart-grid"),
    tickFill: readMdcCssVar("--mdc-chart-tick"),
    tooltipStyle: {
      backgroundColor: readMdcCssVar("--mdc-chart-tooltip-bg"),
      border: `1px solid ${readMdcCssVar("--mdc-chart-tooltip-border")}`,
      color: readMdcCssVar("--mdc-chart-tooltip-text"),
    },
    exportBackground: readMdcCssVar("--mdc-chart-export-bg"),
    seriesColors: readMdcChartSeries(),
  };
}

export function readMdcTrendColor(trend: string | undefined): string {
  switch (trend) {
    case "up":
      return readMdcCssVar("--mdc-trend-up");
    case "down":
      return readMdcCssVar("--mdc-trend-down");
    default:
      return readMdcCssVar("--mdc-trend-stable");
  }
}
