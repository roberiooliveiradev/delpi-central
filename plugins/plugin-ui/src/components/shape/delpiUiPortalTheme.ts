import type { CSSProperties } from "react";

const THEME_SOURCE_VARS = [
  "--delpi-ui-accent",
  "--delpi-ui-surface",
  "--delpi-ui-text",
  "--delpi-ui-border",
  "--delpi-ui-muted",
  "--td-accent",
  "--td-surface",
  "--td-text",
  "--td-border",
  "--td-muted",
  "--surface",
  "--text",
  "--border",
  "--primary",
  "--text-muted",
] as const;

export type DelpiUiPortalTheme = {
  dataTheme?: string;
  style: CSSProperties;
};

function resolveThemeAttribute(anchor?: HTMLElement | null): string | undefined {
  if (typeof document === "undefined") return undefined;

  const themed =
    anchor?.closest("[data-theme]") ?? document.documentElement;
  const explicit = themed.getAttribute("data-theme");
  if (explicit === "light" || explicit === "dark") return explicit;

  if (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(prefers-color-scheme: dark)").matches
  ) {
    return "dark";
  }
  return "light";
}

function findThemeSource(anchor?: HTMLElement | null): HTMLElement | null {
  if (typeof document === "undefined") return null;

  let source: HTMLElement | null = anchor ?? null;
  while (source) {
    const computed = getComputedStyle(source);
    if (
      computed.getPropertyValue("--delpi-ui-surface").trim() ||
      computed.getPropertyValue("--td-surface").trim()
    ) {
      return source;
    }
    source = source.parentElement;
  }

  return (
    document.querySelector(".dashboard-tv-dashboard") ??
    document.querySelector("[class*='dashboard-']") ??
    document.documentElement
  );
}

/** Copia tokens do host do plugin para portais no `body`. */
export function resolveDelpiUiPortalTheme(anchor?: HTMLElement | null): DelpiUiPortalTheme {
  if (typeof document === "undefined") {
    return { style: {} };
  }

  const source = findThemeSource(anchor);
  const computed = source ? getComputedStyle(source) : getComputedStyle(document.documentElement);
  const style: Record<string, string> = {};

  for (const key of THEME_SOURCE_VARS) {
    const value = computed.getPropertyValue(key).trim();
    if (value) style[key] = value;
  }

  const accent = style["--delpi-ui-accent"] ?? style["--td-accent"] ?? style["--primary"];
  const surface = style["--delpi-ui-surface"] ?? style["--td-surface"] ?? style["--surface"];
  const text = style["--delpi-ui-text"] ?? style["--td-text"] ?? style["--text"];
  const border = style["--delpi-ui-border"] ?? style["--td-border"] ?? style["--border"];
  const muted =
    style["--delpi-ui-muted"] ??
    style["--td-muted"] ??
    style["--text-muted"] ??
    (text ? `color-mix(in srgb, ${text} 55%, transparent)` : "");

  if (accent) style["--delpi-ui-accent"] = accent;
  if (surface) style["--delpi-ui-surface"] = surface;
  if (text) style["--delpi-ui-text"] = text;
  if (border) style["--delpi-ui-border"] = border;
  if (muted) style["--delpi-ui-muted"] = muted;

  return {
    dataTheme: resolveThemeAttribute(anchor),
    style,
  };
}

export const DELPI_UI_SHAPE_THEME_HOST_CLASS = "delpi-ui-shape-theme-host";
