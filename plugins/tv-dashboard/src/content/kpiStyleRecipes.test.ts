import { DECK_KPI_DEFAULTS } from "@delpi/plugin-ui/index";
import { describe, expect, it } from "vitest";

import {
  KPI_APPEARANCE_RECIPES,
  KPI_TONE_OPTIONS,
  applyKpiAppearanceRecipe,
  applyKpiTone,
  isKpiAppearanceRecipeActive,
  isKpiToneActive,
} from "./kpiStyleRecipes";

describe("kpiStyleRecipes", () => {
  it("appearance recipes são só Claro e Escuro (tom fica ortogonal)", () => {
    expect(KPI_APPEARANCE_RECIPES.map((r) => r.id)).toEqual(["claro", "escuro"]);
    expect(KPI_APPEARANCE_RECIPES.some((r) => r.id === ("positivo" as never))).toBe(false);
  });

  it("Claro permanece ativo quando o tom semântico muda depois", () => {
    const claro = KPI_APPEARANCE_RECIPES.find((r) => r.id === "claro")!;
    const positive = KPI_TONE_OPTIONS.find((t) => t.value === "positive")!;
    const themed = applyKpiAppearanceRecipe(claro, {});
    const withTone = applyKpiTone(positive, themed);

    expect(isKpiAppearanceRecipeActive(claro, withTone)).toBe(true);
    expect(isKpiToneActive(positive, withTone)).toBe(true);
    expect(withTone.backgroundColor ?? DECK_KPI_DEFAULTS.backgroundColor).toBe(
      DECK_KPI_DEFAULTS.backgroundColor,
    );
  });

  it("Escuro não fica ativo só porque o tom é positivo", () => {
    const escuro = KPI_APPEARANCE_RECIPES.find((r) => r.id === "escuro")!;
    const positive = KPI_TONE_OPTIONS.find((t) => t.value === "positive")!;
    const lightPositive = applyKpiTone(positive, {
      backgroundColor: DECK_KPI_DEFAULTS.backgroundColor,
      tone: "default",
    });

    expect(isKpiAppearanceRecipeActive(escuro, lightPositive)).toBe(false);
    expect(isKpiToneActive(positive, lightPositive)).toBe(true);
  });

  it("aplicar Escuro redefine fundo e tom padrão", () => {
    const escuro = KPI_APPEARANCE_RECIPES.find((r) => r.id === "escuro")!;
    const next = applyKpiAppearanceRecipe(escuro, {
      tone: "positive",
      backgroundColor: DECK_KPI_DEFAULTS.backgroundColor,
    });
    expect(next.backgroundColor).toBe("#0f172a");
    expect(next.tone).toBe("default");
    expect(isKpiAppearanceRecipeActive(escuro, next)).toBe(true);
  });
});
