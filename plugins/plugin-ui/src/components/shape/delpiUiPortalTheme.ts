import type { CSSProperties } from "react";

const THEME_SOURCE_VARS = [
  "--delpi-ui-accent",
  "--delpi-ui-surface",
  "--delpi-ui-popover-bg",
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
  if (surface) {
    style["--delpi-ui-surface"] = surface;
    /* Popovers no body compartilham o mesmo fundo do host (Forma, cor, Lucide…). */
    style["--delpi-ui-popover-bg"] = style["--delpi-ui-popover-bg"] || surface;
  }
  if (text) style["--delpi-ui-text"] = text;
  if (border) style["--delpi-ui-border"] = border;
  if (muted) style["--delpi-ui-muted"] = muted;

  /* Tokens do select portado (painel no body sem ancestral `.delpi-ui-select`). */
  if (surface) style["--delpi-ui-select-bg"] = surface;
  if (text) style["--delpi-ui-select-text"] = text;
  if (border) style["--delpi-ui-select-border"] = border;
  if (muted) style["--delpi-ui-select-muted"] = muted;
  if (accent) style["--delpi-ui-select-accent"] = accent;

  return {
    dataTheme: resolveThemeAttribute(anchor),
    style,
  };
}

export const DELPI_UI_SHAPE_THEME_HOST_CLASS = "delpi-ui-shape-theme-host";

/** Hosts MFE reconhecidos para portais contidos (anti-vazamento / sidebar). */
const MFE_HOST_SCOPE_RE = /^(dashboard-[a-z0-9-]+|minha-delpi-chat)$/i;

function firstMfeHostScopeClass(classList: DOMTokenList): string | undefined {
  for (const className of Array.from(classList)) {
    if (MFE_HOST_SCOPE_RE.test(className)) return className;
  }
  return undefined;
}

/**
 * Resolve a classe de escopo do plugin para portais no `body`.
 * Preferência: prop explícita; senão ancestral `.dashboard-*` / `minha-delpi-chat` do âncora.
 * Sem escopo, seletores `.dashboard-* .{prefix}-select__*` não aplicam no painel portado.
 */
export function resolveMfePortalScopeClassName(
  anchor?: HTMLElement | null,
  explicit?: string,
): string | undefined {
  const trimmed = explicit?.trim();
  if (trimmed) return trimmed;
  if (!anchor) return undefined;

  let node: HTMLElement | null = anchor;
  while (node) {
    const scope = firstMfeHostScopeClass(node.classList);
    if (scope) return scope;
    node = node.parentElement;
  }
  return undefined;
}

/**
 * Resolve o elemento host do MFE para modais contidos.
 * Preferência: prop explícita → ancestral do âncora → primeiro host visível no documento.
 */
export function resolveMfeHostElement(options?: {
  anchor?: HTMLElement | null;
  portalScopeClassName?: string;
}): HTMLElement | null {
  if (typeof document === "undefined") return null;

  const explicit = options?.portalScopeClassName?.trim();
  if (explicit) {
    const first = explicit.split(/\s+/)[0];
    if (!first || !/^[a-zA-Z0-9_-]+$/.test(first)) return null;
    return document.querySelector<HTMLElement>(`.${first}`);
  }

  let node: HTMLElement | null = options?.anchor ?? null;
  while (node) {
    if (firstMfeHostScopeClass(node.classList)) return node;
    node = node.parentElement;
  }

  const candidates = Array.from(
    document.querySelectorAll<HTMLElement>("[class*='dashboard-'], .minha-delpi-chat"),
  ).filter((el) => firstMfeHostScopeClass(el.classList));

  return (
    candidates.find((el) => el.getClientRects().length > 0) ??
    candidates[0] ??
    null
  );
}
