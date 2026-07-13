import { describe, expect, it } from "vitest";
import { mergeComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import {
  CHART_COLOR_PALETTES,
  CHART_STYLE_RECIPES,
  applyChartColorPalette,
  applyChartStyleRecipe,
} from "./chartStyleRecipes";

describe("chartStyleRecipes", () => {
  it("expõe paletas e estilos Delpi", () => {
    expect(CHART_COLOR_PALETTES.length).toBeGreaterThanOrEqual(4);
    expect(CHART_STYLE_RECIPES.length).toBeGreaterThanOrEqual(3);
  });

  it("applyChartColorPalette define seriesColor", () => {
    const palette = CHART_COLOR_PALETTES[0]!;
    const next = applyChartColorPalette(palette, mergeComunicadoChartOptions({}));
    expect(next.seriesColor).toBe(palette.seriesColor);
  });

  it("applyChartStyleRecipe — sem grade", () => {
    const recipe = CHART_STYLE_RECIPES.find((item) => item.id === "clean");
    expect(recipe).toBeTruthy();
    const next = applyChartStyleRecipe(recipe!, mergeComunicadoChartOptions({ showGrid: true }));
    expect(next.showGrid).toBe(false);
  });
});
