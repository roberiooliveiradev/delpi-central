import type { TableStylePreset } from "@delpi/plugin-ui/index";
import { resolveAutomaticTextColor } from "@delpi/plugin-ui/index";
import type {
  ComunicadoTableOptions,
  ComunicadoTablePartsMap,
  ComunicadoTablePreset,
} from "@delpi/tv-dashboard-presentation";
import {
  clearTablePartThemePaint,
  mergeComunicadoTableOptions,
  mergeTablePartsWithOptions,
} from "@delpi/tv-dashboard-presentation";

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

const INK = DELPI_THEME.ink;
const ON_DARK = "#f8fafc";

/** Fundo transparente (minimal) — contraste como sobre branco. */
function contrastBg(background: string | undefined, fallback: string): string {
  const value = (background ?? fallback).trim().toLowerCase();
  if (!value || value === "transparent") return fallback;
  return background ?? fallback;
}

/**
 * Garante header/célula com pares fundo+texto legíveis.
 * Sempre define as quatro chaves para a troca de estilo sobrescrever tema anterior.
 */
export function normalizeTableStyleRecipeOptions(
  options: Partial<ComunicadoTableOptions>,
): Partial<ComunicadoTableOptions> {
  const headerBg = options.headerBg ?? "#e2e8f0";
  const cellBg = options.cellBg ?? "#ffffff";
  const headerTextColor =
    options.headerTextColor ??
    resolveAutomaticTextColor(contrastBg(headerBg, "#ffffff"));
  const cellTextColor =
    options.cellTextColor ??
    resolveAutomaticTextColor(contrastBg(cellBg, "#ffffff"));
  return {
    ...options,
    headerBg,
    cellBg,
    headerTextColor,
    cellTextColor,
  };
}

/**
 * Aplica receita de galeria: cores completas + limpa fill/color órfãos em partes.
 */
export function buildTableStyleRecipeApplication(params: {
  currentOptions?: ComunicadoTableOptions | null;
  currentParts?: ComunicadoTablePartsMap | null;
  recipe: TableStyleRecipe;
}): {
  tableOptions: ComunicadoTableOptions;
  tableParts: ComunicadoTablePartsMap;
  tablePreset: ComunicadoTablePreset;
} {
  const theme = normalizeTableStyleRecipeOptions(params.recipe.options);
  const tableOptions = mergeComunicadoTableOptions(
    {
      ...(params.currentOptions ?? {}),
      ...theme,
    },
    params.recipe.preset,
  );
  /* Força o tema da receita (merge com preset não pode reintroduzir texto antigo). */
  tableOptions.headerBg = theme.headerBg;
  tableOptions.cellBg = theme.cellBg;
  tableOptions.headerTextColor = theme.headerTextColor;
  tableOptions.cellTextColor = theme.cellTextColor;
  if (theme.showBorders != null) tableOptions.showBorders = theme.showBorders;
  if (theme.zebraStripe != null) tableOptions.zebraStripe = theme.zebraStripe;
  if (theme.borderColor != null) tableOptions.borderColor = theme.borderColor;

  const tableParts = mergeTablePartsWithOptions(
    clearTablePartThemePaint(params.currentParts),
    tableOptions,
  );
  return {
    tableOptions,
    tableParts,
    tablePreset: params.recipe.preset,
  };
}

/**
 * Galeria compacta Claros / Médios / Escuros — thumbs mapeiam a tablePreset + options.
 * Toda receita declara cellTextColor + headerTextColor (legibilidade na troca).
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
      headerTextColor: INK,
      cellBg: "#ffffff",
      cellTextColor: INK,
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
      cellTextColor: INK,
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
      headerTextColor: INK,
      cellBg: "transparent",
      cellTextColor: INK,
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
      cellTextColor: INK,
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
      cellTextColor: INK,
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
      cellTextColor: INK,
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
      cellTextColor: INK,
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
      cellTextColor: ON_DARK,
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

/** Adapta receitas do deck para o strip/galeria canônicos do plugin-ui. */
export function tableStyleRecipesAsPresets(
  recipes: readonly TableStyleRecipe[] = TABLE_STYLE_RECIPES,
): TableStylePreset[] {
  return recipes.map((recipe) => {
    const theme = normalizeTableStyleRecipeOptions(recipe.options);
    return {
      id: recipe.id,
      label: recipe.label,
      category: recipe.category,
      headerBg: theme.headerBg ?? "#e2e8f0",
      cellBg: theme.cellBg ?? "#ffffff",
      borderColor: recipe.options.borderColor ?? "#cbd5e1",
    };
  });
}

export function findTableStyleRecipe(id: string): TableStyleRecipe | undefined {
  return TABLE_STYLE_RECIPES.find((recipe) => recipe.id === id);
}

/** Match aproximado do estilo ativo (header + preset). */
export function resolveActiveTableStyleRecipeId(
  options: ComunicadoTableOptions,
  preset: ComunicadoTablePreset,
): string | undefined {
  const match = TABLE_STYLE_RECIPES.find(
    (recipe) =>
      recipe.preset === preset &&
      (recipe.options.headerBg ?? null) === (options.headerBg ?? null) &&
      (recipe.options.cellBg ?? null) === (options.cellBg ?? null),
  );
  return match?.id;
}
