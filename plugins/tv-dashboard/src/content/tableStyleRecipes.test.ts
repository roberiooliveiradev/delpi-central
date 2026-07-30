import { describe, expect, it } from "vitest";

import {
  buildTableStyleRecipeApplication,
  findTableStyleRecipe,
  normalizeTableStyleRecipeOptions,
  TABLE_STYLE_RECIPES,
  tableStyleRecipesAsPresets,
  tableStyleRecipesByCategory,
} from "./tableStyleRecipes";

describe("tableStyleRecipes", () => {
  it("expõe receitas Claros/Médios/Escuros com preset Delpi", () => {
    expect(TABLE_STYLE_RECIPES.length).toBeGreaterThanOrEqual(8);
    expect(tableStyleRecipesByCategory("light").length).toBeGreaterThan(0);
    expect(tableStyleRecipesByCategory("medium").length).toBeGreaterThan(0);
    expect(tableStyleRecipesByCategory("dark").length).toBeGreaterThan(0);
    for (const recipe of TABLE_STYLE_RECIPES) {
      expect(["grid", "minimal", "banded"]).toContain(recipe.preset);
      expect(recipe.options).toBeTruthy();
    }
  });

  it("toda receita declara pares fundo+texto legíveis", () => {
    for (const recipe of TABLE_STYLE_RECIPES) {
      const theme = normalizeTableStyleRecipeOptions(recipe.options);
      expect(theme.headerTextColor).toBeTruthy();
      expect(theme.cellTextColor).toBeTruthy();
      expect(theme.headerBg).toBeTruthy();
      expect(theme.cellBg).toBeTruthy();
    }
  });

  it("adapta receitas para presets do plugin-ui", () => {
    const presets = tableStyleRecipesAsPresets();
    expect(presets).toHaveLength(TABLE_STYLE_RECIPES.length);
    expect(findTableStyleRecipe(presets[0]!.id)?.id).toBe(presets[0]!.id);
    expect(presets[0]!.headerBg).toBeTruthy();
  });

  it("troca de escuro → claro sobrescreve cellTextColor claro e limpa paint", () => {
    const dark = findTableStyleRecipe("dark-purple")!;
    const light = findTableStyleRecipe("medium-teal")!;
    const fromDark = buildTableStyleRecipeApplication({
      currentOptions: { cellTextColor: "#f3e8ff", cellBg: "#1a1028" },
      currentParts: {
        "cell:0:0": { style: { color: "#ffffff", fill: "#112233" } },
        title: { content: "Topo", style: { color: "#fff", fontSize: 18 } },
        frame: { style: { fill: "#fff", borderRadius: 8 } },
      },
      recipe: dark,
    });
    expect(fromDark.tableOptions.cellTextColor).toBe("#f3e8ff");

    const toLight = buildTableStyleRecipeApplication({
      currentOptions: fromDark.tableOptions,
      currentParts: fromDark.tableParts,
      recipe: light,
    });
    expect(toLight.tableOptions.cellTextColor).toBe("#0f172a");
    expect(toLight.tableOptions.cellBg).toBe("#f8fafc");
    expect(toLight.tableOptions.headerTextColor).toBe("#ffffff");
    expect(toLight.tableParts["cell:0:0"]?.style?.color).toBeUndefined();
    expect(toLight.tableParts["cell:0:0"]?.style?.fill).toBeUndefined();
    expect(toLight.tableParts.title?.content).toBe("Topo");
    expect(toLight.tableParts.title?.style?.fontSize).toBe(18);
    expect(toLight.tableParts.frame?.style?.borderRadius).toBe(8);
  });
});
