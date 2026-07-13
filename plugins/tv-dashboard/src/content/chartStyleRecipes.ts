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
  },
  {
    id: "teal",
    label: "Teal",
    seriesColor: "#0f766e",
    colors: ["#0f766e", "#14b8a6", "#115e59", "#5eead4"],
  },
  {
    id: "orange",
    label: "Âmbar",
    seriesColor: "#f2a100",
    colors: ["#f2a100", "#fbbf24", "#b45309", "#fde68a"],
  },
  {
    id: "navy",
    label: "Marinho",
    seriesColor: "#003866",
    colors: ["#003866", "#1e40af", "#089bdb", "#93c5fd"],
  },
  {
    id: "purple",
    label: "Roxo",
    seriesColor: "#7e14ff",
    colors: ["#7e14ff", "#a855f7", "#5b21b6", "#d8b4fe"],
  },
  {
    id: "green",
    label: "Verde",
    seriesColor: "#2e7d32",
    colors: ["#2e7d32", "#4caf50", "#1b5e20", "#a5d6a7"],
  },
];

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
 * Em gráfico com **uma** série, a linha/barra usa a cor principal; a 2ª entra no fill da área.
 */
export function applyChartColorPalette(
  palette: ChartColorPalette,
  options: ComunicadoChartOptions,
): ComunicadoChartOptions {
  return {
    ...options,
    seriesColor: palette.seriesColor,
    categoryColors: [...palette.colors],
  };
}

export function applyChartStyleRecipe(
  recipe: ChartStyleRecipe,
  options: ComunicadoChartOptions,
): ComunicadoChartOptions {
  return { ...options, ...recipe.patch };
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
