import { buildThemeColorGrid } from "./colorUtils";

/** Dez cores-base do tema DELPI (colunas da grade 10×6). */
export const DELPI_THEME_BASE_COLORS = [
  "#ffffff",
  "#000000",
  "#44546a",
  "#089bdb",
  "#003866",
  "#47bfff",
  "#7e14ff",
  "#2e7d32",
  "#f2a100",
  "#e53935",
] as const;

/** Grade 6×10 derivada das cores-base (linhas = variações). */
export const DELPI_THEME_COLOR_GRID = buildThemeColorGrid(DELPI_THEME_BASE_COLORS);

/** Dez cores padrão (linha «Cores Padrão» estilo Office). */
export const DELPI_STANDARD_COLORS = [
  "#ffffff",
  "#000000",
  "#e7e6e6",
  "#44546a",
  "#4472c4",
  "#ed7d31",
  "#a5a5a5",
  "#ffc000",
  "#5b9bd5",
  "#70ad47",
] as const;

/** Hexágonos da aba Padrão do diálogo «Mais cores». */
export const DELPI_DIALOG_STANDARD_COLORS = [
  "#f44336",
  "#e91e63",
  "#9c27b0",
  "#673ab7",
  "#3f51b5",
  "#2196f3",
  "#03a9f4",
  "#00bcd4",
  "#009688",
  "#4caf50",
  "#8bc34a",
  "#cddc39",
  "#ffeb3b",
  "#ffc107",
  "#ff9800",
  "#ff5722",
  "#795548",
  "#9e9e9e",
  "#607d8b",
  "#000000",
] as const;
