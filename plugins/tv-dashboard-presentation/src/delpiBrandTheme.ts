/**
 * Loader do padrão de marca Delpi (claro/escuro + logo).
 * Conteúdo: ``content/delpiBrandTheme.json`` — sem hex/frames espalhados no código.
 */

import rawTheme from "./content/delpiBrandTheme.json";

export type DelpiBrandModeKey = "dark" | "light";

export type DelpiBrandLogoVariant = "onDark" | "onLight";

export type DelpiBrandColors = {
  bgFrom: string;
  bgTo: string;
  bgSolid: string;
  navy: string;
  card: string;
  accent: string;
  accentSoft: string;
  accentMuted: string;
  accentWash: string;
  accentBorderSoft: string;
  onBg: string;
  onBgMuted: string;
  onCard: string;
  onCardMuted: string;
  shapeStroke: string;
  ink: string;
  surface: string;
  surfaceMuted: string;
  borderMuted: string;
};

export type DelpiBrandMode = {
  key: DelpiBrandModeKey;
  label: string;
  logoVariant: DelpiBrandLogoVariant;
  background:
    | { type: "color"; value: string }
    | { type: "gradient"; from: string; to: string; angle?: number };
  colors: DelpiBrandColors;
  seriesPalette: string[];
};

export type DelpiBrandLogoConfig = {
  safeMarginPct: number;
  widthPct: number;
  heightPct: number;
  opacity: number;
  corner: "bottom-right" | "bottom-left" | "top-right" | "top-left";
  backgroundPosition: string;
  zIndex: number;
  parseFallback: { dark: string; light: string };
};

export type DelpiBrandThemeDocument = {
  version: string;
  owner: string;
  summary?: string;
  luminanceThreshold: number;
  modes: Record<DelpiBrandModeKey, DelpiBrandMode>;
  logo: DelpiBrandLogoConfig;
  slideThemeBindings: Array<{ key: string; label: string; mode: DelpiBrandModeKey }>;
};

const theme = rawTheme as DelpiBrandThemeDocument;

export function getDelpiBrandTheme(): DelpiBrandThemeDocument {
  return theme;
}

export function getDelpiBrandMode(mode: DelpiBrandModeKey): DelpiBrandMode {
  return theme.modes[mode];
}

export function getDelpiBrandColors(mode: DelpiBrandModeKey): DelpiBrandColors {
  return theme.modes[mode].colors;
}

/** Accent canônico Delpi (igual nos dois modos). */
export function getDelpiBrandAccent(): string {
  return theme.modes.dark.colors.accent;
}

export function getDelpiBrandLuminanceThreshold(): number {
  return theme.luminanceThreshold;
}

export function getDelpiBrandLogoConfig(): DelpiBrandLogoConfig {
  return theme.logo;
}

/** Frame % derivado do JSON (canto + margem + tamanho). */
export function resolveDelpiBrandLogoFrame(
  logo: DelpiBrandLogoConfig = theme.logo,
): { x: number; y: number; w: number; h: number } {
  const margin = logo.safeMarginPct;
  const w = logo.widthPct;
  const h = logo.heightPct;
  switch (logo.corner) {
    case "bottom-left":
      return { x: margin, y: 100 - h - margin, w, h };
    case "top-right":
      return { x: 100 - w - margin, y: margin, w, h };
    case "top-left":
      return { x: margin, y: margin, w, h };
    case "bottom-right":
    default:
      return { x: 100 - w - margin, y: 100 - h - margin, w, h };
  }
}

/** Snapshot flat compatível com designTokens.brand das recipes (modo escuro TV). */
export function delpiBrandTokensForRecipes(mode: DelpiBrandModeKey = "dark"): {
  bgFrom: string;
  bgTo: string;
  card: string;
  accent: string;
  onCard: string;
  onCardMuted: string;
  onBg: string;
} {
  const c = theme.modes[mode].colors;
  return {
    bgFrom: c.bgFrom,
    bgTo: c.bgTo,
    card: c.card,
    accent: c.accent,
    onCard: c.onCard,
    onCardMuted: c.onCardMuted,
    onBg: c.onBg,
  };
}
