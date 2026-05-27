import { useEffect, useState } from "react";

/** Lê tokens --mdc-* do :root (portal + plugin). */

function detectDarkMode(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const root = document.documentElement;

  if (root.getAttribute("data-theme") === "dark") {
    return true;
  }

  if (root.getAttribute("data-theme") === "light") {
    return false;
  }

  return (
    root.classList.contains("dark") ||
    document.body.classList.contains("dark") ||
    window.matchMedia("(prefers-color-scheme: dark)").matches
  );
}

/** Reage a data-theme, classe .dark e prefers-color-scheme. */
export function useMdcDarkMode(): boolean {
  const [isDark, setIsDark] = useState(detectDarkMode);

  useEffect(() => {
    const root = document.documentElement;
    const media = window.matchMedia("(prefers-color-scheme: dark)");

    const refresh = () => setIsDark(detectDarkMode());

    const observer = new MutationObserver(refresh);
    observer.observe(root, {
      attributes: true,
      attributeFilter: ["data-theme", "class"],
    });
    observer.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
    });
    media.addEventListener("change", refresh);

    return () => {
      observer.disconnect();
      media.removeEventListener("change", refresh);
    };
  }, []);

  return isDark;
}

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
