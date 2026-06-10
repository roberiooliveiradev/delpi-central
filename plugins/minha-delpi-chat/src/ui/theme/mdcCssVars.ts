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

const CHART_SERIES_FALLBACK_LIGHT = [
  "#0478b5",
  "#0d6e8c",
  "#067647",
  "#b45309",
  "#b42318",
  "#5b21b6",
  "#0369a1",
  "#15803d",
  "#9f1239",
  "#003866",
] as const;

const CHART_SERIES_FALLBACK_DARK = [
  "#38bdf8",
  "#2dd4bf",
  "#4ade80",
  "#fbbf24",
  "#f87171",
  "#a78bfa",
  "#60a5fa",
  "#86efac",
  "#fb7185",
  "#93c5fd",
] as const;

function sanitizeChartColors(colors: string[] | undefined): string[] {
  if (!Array.isArray(colors)) {
    return [];
  }

  return colors.map((color) => color.trim()).filter(Boolean);
}

export function readMdcChartSeries(count = 10): string[] {
  const colors: string[] = [];

  for (let index = 1; index <= count; index += 1) {
    colors.push(readMdcCssVar(`--mdc-chart-series-${index}`, readMdcCssVar("--mdc-primary")));
  }

  return sanitizeChartColors(colors);
}

/** Paleta efetiva: config da API → tokens CSS → fallback saturado por tema. */
export function resolveChartSeriesColors(
  configColors: string[] | undefined,
  isDark: boolean,
): string[] {
  const fromConfig = sanitizeChartColors(configColors);

  if (fromConfig.length > 0) {
    return fromConfig;
  }

  const fromCss = readMdcChartSeries();

  if (fromCss.length > 0) {
    return fromCss;
  }

  return [...(isDark ? CHART_SERIES_FALLBACK_DARK : CHART_SERIES_FALLBACK_LIGHT)];
}

export function resolveChartSeriesColor(
  colors: string[],
  index: number,
  isDark: boolean,
): string {
  if (colors.length > 0) {
    return colors[index % colors.length] || colors[0];
  }

  const fallback = isDark ? CHART_SERIES_FALLBACK_DARK : CHART_SERIES_FALLBACK_LIGHT;
  return fallback[index % fallback.length];
}

export function resolveMermaidTheme(isDark: boolean): "dark" | "default" {
  return isDark ? "dark" : "default";
}

export function readMdcChartTheme(isDark: boolean) {
  return {
    gridColor: readMdcCssVar("--mdc-chart-grid"),
    tickFill: readMdcCssVar("--mdc-chart-tick"),
    tooltipStyle: {
      backgroundColor: readMdcCssVar("--mdc-chart-tooltip-bg"),
      border: `1px solid ${readMdcCssVar("--mdc-chart-tooltip-border")}`,
      color: readMdcCssVar("--mdc-chart-tooltip-text"),
    },
    exportBackground: readMdcCssVar("--mdc-chart-export-bg"),
    seriesColors: resolveChartSeriesColors(undefined, isDark),
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
