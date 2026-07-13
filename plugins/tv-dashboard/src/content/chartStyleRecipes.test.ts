import { describe, expect, it } from "vitest";
import { DECK_THEME_DARK, DECK_THEME_LIGHT } from "@delpi/plugin-ui/index";
import { mergeComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import {
  CHART_COLOR_PALETTES,
  CHART_STYLE_RECIPES,
  applyChartColorPalette,
  applyChartStyleRecipe,
  isChartStyleRecipeActive,
} from "./chartStyleRecipes";

describe("chartStyleRecipes", () => {
  it("expõe paletas e estilos Delpi", () => {
    expect(CHART_COLOR_PALETTES.length).toBeGreaterThanOrEqual(4);
    expect(CHART_STYLE_RECIPES.length).toBeGreaterThanOrEqual(3);
  });

  it("applyChartColorPalette define seriesColor e categoryColors", () => {
    const palette = CHART_COLOR_PALETTES[0]!;
    const next = applyChartColorPalette(palette, mergeComunicadoChartOptions({}));
    expect(next.seriesColor).toBe(palette.seriesColor);
    expect(next.categoryColors).toEqual(palette.colors);
  });

  it("applyChartStyleRecipe — sem grade", () => {
    const recipe = CHART_STYLE_RECIPES.find((item) => item.id === "clean");
    expect(recipe).toBeTruthy();
    const next = applyChartStyleRecipe(recipe!, mergeComunicadoChartOptions({ showGrid: true }));
    expect(next.showGrid).toBe(false);
    expect(next.showVerticalGrid).toBe(false);
  });

  it("applyChartStyleRecipe — escuro define theme + fundo", () => {
    const recipe = CHART_STYLE_RECIPES.find((item) => item.id === "office-dark");
    expect(recipe).toBeTruthy();
    const next = applyChartStyleRecipe(recipe!, mergeComunicadoChartOptions({ theme: "light" }));
    expect(next.theme).toBe("dark");
    expect(next.backgroundColor).toBe(DECK_THEME_DARK.bg);
  });

  it("applyChartStyleRecipe — claro restaura fundo light", () => {
    const recipe = CHART_STYLE_RECIPES.find((item) => item.id === "office-light");
    const next = applyChartStyleRecipe(
      recipe!,
      mergeComunicadoChartOptions({ theme: "dark", backgroundColor: DECK_THEME_DARK.bg }),
    );
    expect(next.theme).toBe("light");
    expect(next.backgroundColor).toBe(DECK_THEME_LIGHT.bg);
  });

  it("isChartStyleRecipeActive marca Escuro", () => {
    const dark = CHART_STYLE_RECIPES.find((item) => item.id === "office-dark")!;
    expect(isChartStyleRecipeActive(dark, { theme: "dark" })).toBe(true);
    expect(isChartStyleRecipeActive(dark, { theme: "light" })).toBe(false);
  });
});
