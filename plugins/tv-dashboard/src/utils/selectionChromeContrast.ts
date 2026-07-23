/**
 * Cores do chrome de seleção (outline, handles, marquee) com contraste
 * contra o fundo do slide — visual oco (fill claro + borda colorida).
 */
import {
  cssToColorValue,
  hexToRgb,
  relativeLuminance,
  rgbToHex,
} from "@delpi/plugin-ui/index";
import type { ComunicadoBackground } from "@delpi/tv-dashboard-presentation";

export type SelectionChromeColors = {
  handleFill: string;
  handleBorder: string;
  outline: string;
  outlineMulti: string;
  marqueeBorder: string;
  marqueeFill: string;
  stem: string;
  /** Contorno do pai enquanto filho está isolado. */
  parentHint: string;
};

const ACCENT_DEFAULT = "#089bdb";
const LIGHT = "#ffffff";
const DARK = "#0f172a";
const PARENT_HINT = "#94a3b8";
/** Contraste mínimo WCAG aproximado para chrome de UI (não texto). */
const MIN_CONTRAST = 3;

function contrastRatio(aHex: string, bHex: string): number {
  const a = relativeLuminance(aHex);
  const b = relativeLuminance(bHex);
  const hi = Math.max(a, b);
  const lo = Math.min(a, b);
  return (hi + 0.05) / (lo + 0.05);
}

function mixHex(a: string, b: string, ratio: number): string {
  const left = hexToRgb(cssToColorValue(a).hex);
  const right = hexToRgb(cssToColorValue(b).hex);
  const t = Math.min(1, Math.max(0, ratio));
  return rgbToHex(
    left.r + (right.r - left.r) * t,
    left.g + (right.g - left.g) * t,
    left.b + (right.b - left.b) * t,
  );
}

/**
 * Amostra representativa do fundo do slide para decidir contraste do chrome.
 * Imagem → cinza médio (força anel dual claro/escuro).
 */
export function resolveSlideBackgroundSample(
  background: ComunicadoBackground | undefined,
): string {
  const bg = background ?? { type: "color" as const, value: "#ffffff" };
  if (bg.type === "color") {
    return cssToColorValue(bg.value || "#ffffff", "#ffffff").hex;
  }
  if (bg.type === "gradient") {
    const from = cssToColorValue(bg.from || DARK, DARK).hex;
    const to = cssToColorValue(bg.to || DARK, DARK).hex;
    return mixHex(from, to, 0.5);
  }
  return "#6b7280";
}

export function resolveSelectionChromeColors(
  background: ComunicadoBackground | undefined,
  accent: string = ACCENT_DEFAULT,
): SelectionChromeColors {
  const bgHex = resolveSlideBackgroundSample(background);
  const accentHex = cssToColorValue(accent, ACCENT_DEFAULT).hex;

  let outline = accentHex;
  if (contrastRatio(outline, bgHex) < MIN_CONTRAST) {
    outline = relativeLuminance(bgHex) >= 0.45 ? DARK : LIGHT;
  }

  /* Handles ocos: fill branco + borda = cor do outline (prints Figma/Canva). */
  const handleFill = LIGHT;
  let handleBorder = outline;
  if (contrastRatio(handleBorder, handleFill) < MIN_CONTRAST) {
    handleBorder = DARK;
  }

  return {
    handleFill,
    handleBorder,
    outline: handleBorder,
    outlineMulti: mixHex(handleBorder, LIGHT, 0.35),
    marqueeBorder: handleBorder,
    marqueeFill: handleBorder,
    stem: handleBorder,
    parentHint: PARENT_HINT,
  };
}

/** CSS custom properties para o canvas do composer. */
export function selectionChromeContrastCssVars(
  colors: SelectionChromeColors,
): Record<string, string> {
  return {
    "--td-selection-handle-fill": colors.handleFill,
    "--td-selection-handle-border": colors.handleBorder,
    "--td-selection-outline": colors.outline,
    "--td-selection-outline-multi": colors.outlineMulti,
    "--td-selection-marquee-border": colors.marqueeBorder,
    "--td-selection-marquee-fill": colors.marqueeFill,
    "--td-selection-stem": colors.stem,
    "--td-selection-parent-hint": colors.parentHint,
  };
}
