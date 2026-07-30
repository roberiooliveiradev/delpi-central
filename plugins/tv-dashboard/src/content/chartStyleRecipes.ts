import {
  DECK_THEME_DARK,
  DECK_THEME_LIGHT,
} from "@delpi/plugin-ui/index";
import type { ComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

/** Paleta de série (swatches) — Alterar Cores. */
export type ChartColorPalette = {
  id: string;
  label: string;
  /** Cor principal da série (`seriesColor`). */
  seriesColor: string;
  colors: string[];
  /** Categórica (tons) vs escala semântica (melhor/pior). Default: categorical. */
  kind?: "categorical" | "semantic";
  /** Tooltip / aria complementar. */
  hint?: string;
};

/** Estilo visual compacto — theme + grade + fundo. */
export type ChartStyleRecipe = {
  id: string;
  label: string;
  patch: Partial<ComunicadoChartOptions>;
};

export const CHART_COLOR_PALETTES: ChartColorPalette[] = [
  {
    id: "delpi-blue",
    label: "Azul Delpi",
    seriesColor: "#089bdb",
    colors: ["#089bdb", "#47bfff", "#003866", "#7dd3fc"],
    kind: "categorical",
  },
  {
    id: "teal",
    label: "Teal",
    seriesColor: "#0f766e",
    colors: ["#0f766e", "#14b8a6", "#115e59", "#5eead4"],
    kind: "categorical",
  },
  {
    id: "orange",
    label: "Âmbar",
    seriesColor: "#f2a100",
    colors: ["#f2a100", "#fbbf24", "#b45309", "#fde68a"],
    kind: "categorical",
  },
  {
    id: "navy",
    label: "Marinho",
    seriesColor: "#003866",
    colors: ["#003866", "#1e40af", "#089bdb", "#93c5fd"],
    kind: "categorical",
  },
  {
    id: "purple",
    label: "Roxo",
    seriesColor: "#7e14ff",
    colors: ["#7e14ff", "#a855f7", "#5b21b6", "#d8b4fe"],
    kind: "categorical",
  },
  {
    id: "green",
    label: "Verde",
    seriesColor: "#2e7d32",
    colors: ["#2e7d32", "#4caf50", "#1b5e20", "#a5d6a7"],
    kind: "categorical",
  },
  {
    id: "red",
    label: "Vermelho",
    seriesColor: "#9f1239",
    colors: ["#9f1239", "#e11d48", "#be123c", "#fb7185"],
    kind: "categorical",
  },
  {
    id: "gray",
    label: "Cinza",
    seriesColor: "#1f2937",
    colors: ["#1f2937", "#4b5563", "#9ca3af", "#d1d5db"],
    kind: "categorical",
  },
  {
    id: "rag-good-first",
    label: "Melhor → pior",
    seriesColor: "#15803d",
    colors: ["#15803d", "#089bdb", "#eab308", "#f97316", "#be123c"],
    kind: "semantic",
    hint: "1ª categoria/fatia boa; última ruim (ordem do índice).",
  },
  {
    id: "rag-bad-first",
    label: "Pior → melhor",
    seriesColor: "#be123c",
    colors: ["#be123c", "#f97316", "#eab308", "#089bdb", "#15803d"],
    kind: "semantic",
    hint: "1ª categoria/fatia ruim; última boa (útil em rankings do pior).",
  },
  {
    id: "diverging-pos",
    label: "Divergente (positivo)",
    seriesColor: "#166534",
    colors: ["#166534", "#86efac", "#e5e7eb", "#fda4af", "#be123c"],
    kind: "semantic",
    hint: "Extremos: verde (bom) ↔ vermelho (ruim).",
  },
  {
    id: "diverging-neg",
    label: "Divergente (negativo)",
    seriesColor: "#be123c",
    colors: ["#be123c", "#fda4af", "#e5e7eb", "#86efac", "#166534"],
    kind: "semantic",
    hint: "Extremos: vermelho (ruim) ↔ verde (bom).",
  },
];

export const CHART_SEMANTIC_PALETTE_IDS = [
  "rag-good-first",
  "rag-bad-first",
  "diverging-pos",
  "diverging-neg",
] as const;

export function chartPalettesByKind(kind: "categorical" | "semantic"): ChartColorPalette[] {
  return CHART_COLOR_PALETTES.filter((palette) => (palette.kind ?? "categorical") === kind);
}

export function findChartColorPalette(id: string | null | undefined): ChartColorPalette | undefined {
  if (!id) return undefined;
  return CHART_COLOR_PALETTES.find((palette) => palette.id === id);
}

/** Paleta semântica padrão ao ativar colorir-por-valor. */
export const DEFAULT_VALUE_SCALE_PALETTE_ID = "rag-good-first";

export const CHART_STYLE_RECIPES: ChartStyleRecipe[] = [
  {
    id: "office-light",
    label: "Claro",
    patch: {
      theme: "light",
      backgroundColor: DECK_THEME_LIGHT.bg,
      showGrid: true,
      showVerticalGrid: false,
    },
  },
  {
    id: "office-dark",
    label: "Escuro",
    patch: {
      theme: "dark",
      backgroundColor: DECK_THEME_DARK.bg,
      showGrid: true,
      showVerticalGrid: false,
    },
  },
  {
    id: "clean",
    label: "Sem grade",
    patch: {
      theme: "light",
      backgroundColor: DECK_THEME_LIGHT.bg,
      showGrid: false,
      showVerticalGrid: false,
    },
  },
  {
    id: "markers-on",
    label: "Com marcadores",
    patch: {
      theme: "light",
      backgroundColor: DECK_THEME_LIGHT.bg,
      showMarkers: true,
      showGrid: true,
    },
  },
];

/**
 * Aplica paleta: cor principal da série + `categoryColors` (área/pie/fatias).
 * Escalas semânticas também gravam `colorScale.paletteId` (rampa para colorir-por-valor).
 */
export function applyChartColorPalette(
  palette: ChartColorPalette,
  options: ComunicadoChartOptions,
): ComunicadoChartOptions {
  const next: ComunicadoChartOptions = {
    ...options,
    seriesColor: palette.seriesColor,
    categoryColors: [...palette.colors],
  };
  if ((palette.kind ?? "categorical") === "semantic") {
    next.colorScale = {
      mode: options.colorScale?.mode ?? "off",
      polarity: options.colorScale?.polarity ?? "high_is_bad",
      paletteId: palette.id,
    };
  }
  return next;
}

export function applyChartStyleRecipe(
  recipe: ChartStyleRecipe,
  options: ComunicadoChartOptions,
): ComunicadoChartOptions {
  return { ...options, ...recipe.patch };
}

/** Liga/desliga colorir-por-valor; garante rampa semântica em `categoryColors`. */
export function applyChartColorScaleMode(
  options: ComunicadoChartOptions,
  mode: "off" | "by_value",
  polarity: "high_is_bad" | "high_is_good" = "high_is_bad",
): ComunicadoChartOptions {
  if (mode === "off") {
    return {
      ...options,
      colorScale: {
        mode: "off",
        polarity: options.colorScale?.polarity ?? polarity,
        paletteId: options.colorScale?.paletteId,
      },
    };
  }
  const palette =
    findChartColorPalette(options.colorScale?.paletteId) ??
    findChartColorPalette(DEFAULT_VALUE_SCALE_PALETTE_ID)!;
  return {
    ...options,
    seriesColor: palette.seriesColor,
    categoryColors: [...palette.colors],
    colorScale: {
      mode: "by_value",
      polarity,
      paletteId: palette.id,
    },
  };
}

export function applyChartColorScalePolarity(
  options: ComunicadoChartOptions,
  polarity: "high_is_bad" | "high_is_good",
): ComunicadoChartOptions {
  return {
    ...options,
    colorScale: {
      mode: options.colorScale?.mode ?? "off",
      polarity,
      paletteId: options.colorScale?.paletteId,
    },
  };
}

/** Destaca o thumb ativo (theme / grade / marcadores). */
export function isChartStyleRecipeActive(
  recipe: ChartStyleRecipe,
  options: ComunicadoChartOptions,
): boolean {
  const theme = options.theme ?? "light";
  const showGrid = options.showGrid !== false;
  const showVertical = Boolean(options.showVerticalGrid);
  const showMarkers = options.showMarkers !== false;

  switch (recipe.id) {
    case "office-light":
      return theme === "light" && showGrid && !showVertical;
    case "office-dark":
      return theme === "dark";
    case "clean":
      return !showGrid && !showVertical;
    case "markers-on":
      return showMarkers && theme === "light";
    default:
      return false;
  }
}

export function isChartColorPaletteActive(
  palette: ChartColorPalette,
  options: ComunicadoChartOptions,
): boolean {
  if (options.colorScale?.paletteId === palette.id) return true;
  return (
    options.seriesColor === palette.seriesColor &&
    JSON.stringify(options.categoryColors ?? []) === JSON.stringify(palette.colors)
  );
}
