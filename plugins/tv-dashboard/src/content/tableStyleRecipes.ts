import type { ComunicadoTableOptions, ComunicadoTablePreset } from "@delpi/tv-dashboard-presentation";

/** Receita visual Delpi para galeria «Estilos de tabela» (não é matriz Office). */
export type TableStyleRecipe = {
  id: string;
  label: string;
  category: "light" | "medium" | "dark";
  preset: ComunicadoTablePreset;
  options: Partial<ComunicadoTableOptions>;
};

const DELPI_THEME = {
  blue: "#089bdb",
  navy: "#003866",
  teal: "#0f766e",
  orange: "#f2a100",
  purple: "#7e14ff",
  green: "#2e7d32",
  slate: "#44546a",
  ink: "#0f172a",
} as const;

/**
 * Galeria compacta Claros / Médios / Escuros — thumbs mapeiam a tablePreset + options.
 */
export const TABLE_STYLE_RECIPES: TableStyleRecipe[] = [
  {
    id: "light-grid",
    label: "Grade clara",
    category: "light",
    preset: "grid",
    options: {
      showBorders: true,
      zebraStripe: false,
      headerBg: "#e2e8f0",
      headerTextColor: DELPI_THEME.ink,
      cellBg: "#ffffff",
      cellTextColor: DELPI_THEME.ink,
      borderColor: "#cbd5e1",
    },
  },
  {
    id: "light-blue",
    label: "Cabeçalho azul claro",
    category: "light",
    preset: "grid",
    options: {
      showBorders: true,
      zebraStripe: false,
      headerBg: "#dbeafe",
      headerTextColor: DELPI_THEME.navy,
      cellBg: "#ffffff",
      borderColor: "#bfdbfe",
    },
  },
  {
    id: "light-minimal",
    label: "Minimalista",
    category: "light",
    preset: "minimal",
    options: {
      showBorders: false,
      zebraStripe: false,
      headerBg: "transparent",
      headerTextColor: DELPI_THEME.ink,
      cellBg: "transparent",
    },
  },
  {
    id: "medium-banded",
    label: "Faixas médias",
    category: "medium",
    preset: "banded",
    options: {
      showBorders: true,
      zebraStripe: true,
      headerBg: DELPI_THEME.blue,
      headerTextColor: "#ffffff",
      cellBg: "#ffffff",
      borderColor: "#e2e8f0",
    },
  },
  {
    id: "medium-teal",
    label: "Teal banded",
    category: "medium",
    preset: "banded",
    options: {
      showBorders: true,
      zebraStripe: true,
      headerBg: DELPI_THEME.teal,
      headerTextColor: "#ffffff",
      cellBg: "#f8fafc",
      borderColor: "#ccfbf1",
    },
  },
  {
    id: "medium-orange",
    label: "Laranja Delpi",
    category: "medium",
    preset: "banded",
    options: {
      showBorders: true,
      zebraStripe: true,
      headerBg: DELPI_THEME.orange,
      headerTextColor: "#ffffff",
      cellBg: "#fffbeb",
      borderColor: "#fde68a",
    },
  },
  {
    id: "medium-navy",
    label: "Marinho",
    category: "medium",
    preset: "grid",
    options: {
      showBorders: true,
      zebraStripe: false,
      headerBg: DELPI_THEME.navy,
      headerTextColor: "#ffffff",
      cellBg: "#ffffff",
      borderColor: "#94a3b8",
    },
  },
  {
    id: "dark-ink",
    label: "Escuro tinta",
    category: "dark",
    preset: "banded",
    options: {
      showBorders: true,
      zebraStripe: true,
      headerBg: DELPI_THEME.ink,
      headerTextColor: "#ffffff",
      cellBg: "#1e293b",
      cellTextColor: "#f8fafc",
      borderColor: "#334155",
    },
  },
  {
    id: "dark-navy",
    label: "Escuro marinho",
    category: "dark",
    preset: "grid",
    options: {
      showBorders: true,
      zebraStripe: false,
      headerBg: DELPI_THEME.navy,
      headerTextColor: "#ffffff",
      cellBg: "#0b1220",
      cellTextColor: "#e2e8f0",
      borderColor: "#1e3a5f",
    },
  },
  {
    id: "dark-purple",
    label: "Escuro roxo",
    category: "dark",
    preset: "banded",
    options: {
      showBorders: true,
      zebraStripe: true,
      headerBg: DELPI_THEME.purple,
      headerTextColor: "#ffffff",
      cellBg: "#1a1028",
      cellTextColor: "#f3e8ff",
      borderColor: "#4c1d95",
    },
  },
];

export function tableStyleRecipesByCategory(
  category: TableStyleRecipe["category"],
): TableStyleRecipe[] {
  return TABLE_STYLE_RECIPES.filter((recipe) => recipe.category === category);
}
