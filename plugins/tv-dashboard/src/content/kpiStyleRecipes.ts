import type { ComunicadoKpiOptions } from "@delpi/tv-dashboard-presentation";
import { DECK_KPI_DEFAULTS } from "@delpi/plugin-ui/index";

export type KpiAppearanceRecipe = {
  id: string;
  label: string;
  patch: Partial<ComunicadoKpiOptions>;
};

export const KPI_APPEARANCE_RECIPES: KpiAppearanceRecipe[] = [
  {
    id: "claro",
    label: "Claro",
    patch: {
      backgroundColor: DECK_KPI_DEFAULTS.backgroundColor,
      valueColor: "auto",
      tone: "default",
    },
  },
  {
    id: "escuro",
    label: "Escuro",
    patch: {
      backgroundColor: "#0f172a",
      valueColor: "#f8fafc",
      tone: "default",
    },
  },
  {
    id: "positivo",
    label: "Positivo",
    patch: { tone: "positive", valueColor: "auto" },
  },
  {
    id: "negativo",
    label: "Negativo",
    patch: { tone: "negative", valueColor: "auto" },
  },
  {
    id: "atencao",
    label: "Atenção",
    patch: { tone: "warning", valueColor: "auto" },
  },
];

export function isKpiAppearanceRecipeActive(
  recipe: KpiAppearanceRecipe,
  options: ComunicadoKpiOptions,
): boolean {
  const tone = options.tone ?? "default";
  if (recipe.patch.tone && recipe.patch.tone !== tone) return false;
  if (
    recipe.patch.backgroundColor &&
    (options.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor) !== recipe.patch.backgroundColor
  ) {
    return false;
  }
  return true;
}

export function applyKpiAppearanceRecipe(
  recipe: KpiAppearanceRecipe,
  options: ComunicadoKpiOptions,
): ComunicadoKpiOptions {
  return { ...options, ...recipe.patch };
}
