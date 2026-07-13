import { describe, expect, it } from "vitest";

import { TABLE_STYLE_RECIPES, tableStyleRecipesByCategory } from "./tableStyleRecipes";

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
});
