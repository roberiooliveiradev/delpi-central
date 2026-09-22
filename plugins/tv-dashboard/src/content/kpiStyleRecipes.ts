import type { ComunicadoKpiOptions } from "@delpi/tv-dashboard-presentation";
import { DECK_KPI_DEFAULTS } from "@delpi/plugin-ui/index";

export type KpiAppearanceRecipe = {
  id: "claro" | "escuro";
  label: string;
  patch: Partial<ComunicadoKpiOptions>;
};

export type KpiToneOption = {
  id: string;
  value: NonNullable<ComunicadoKpiOptions["tone"]>;
  label: string;
};

/** Tema do card (fundo / contraste) — ortogonal ao tom semântico. */
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
];

/** Tom semântico do valor/ícone — independente do tema Claro/Escuro. */
export const KPI_TONE_OPTIONS: KpiToneOption[] = [
  { id: "default", value: "default", label: "Padrão" },
  { id: "positive", value: "positive", label: "Positivo" },
  { id: "negative", value: "negative", label: "Negativo" },
  { id: "warning", value: "warning", label: "Atenção" },
];

/**
 * Match só por tema (fundo). Tom escolhido depois não desmarca Claro/Escuro.
 */
export function isKpiAppearanceRecipeActive(
  recipe: KpiAppearanceRecipe,
  options: ComunicadoKpiOptions,
): boolean {
  const bg = options.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor;
  const expected = recipe.patch.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor;
  return bg === expected;
}

export function applyKpiAppearanceRecipe(
  recipe: KpiAppearanceRecipe,
  options: ComunicadoKpiOptions,
): ComunicadoKpiOptions {
  return { ...options, ...recipe.patch };
}

export function isKpiToneActive(
  tone: KpiToneOption,
  options: ComunicadoKpiOptions,
): boolean {
  return (options.tone ?? "default") === tone.value;
}

export function applyKpiTone(
  tone: KpiToneOption,
  options: ComunicadoKpiOptions,
): ComunicadoKpiOptions {
  return {
    ...options,
    tone: tone.value,
    valueColor: "auto",
  };
}
