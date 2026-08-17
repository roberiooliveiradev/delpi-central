import { describe, expect, it } from "vitest";
import { DECK_THEME_DARK, DECK_THEME_LIGHT } from "@delpi/plugin-ui/index";
import { mergeComunicadoChartOptions } from "@delpi/tv-dashboard-presentation";

import {
  CHART_COLOR_PALETTES,
  CHART_SEMANTIC_PALETTE_IDS,
  CHART_STYLE_RECIPES,
  applyChartColorPalette,
  applyChartColorScaleMode,
  applyChartStyleRecipe,
  chartPalettesByKind,
  isChartStyleRecipeActive,
} from "./chartStyleRecipes";

describe("chartStyleRecipes", () => {
  it("expõe paletas e estilos Delpi", () => {
    expect(CHART_COLOR_PALETTES.length).toBeGreaterThanOrEqual(4);
    expect(CHART_STYLE_RECIPES.length).toBeGreaterThanOrEqual(3);
  });

  it("inclui paletas Vermelho e Cinza", () => {
    const red = CHART_COLOR_PALETTES.find((item) => item.id === "red");
    const gray = CHART_COLOR_PALETTES.find((item) => item.id === "gray");
    expect(red?.label).toBe("Vermelho");
    expect(red?.colors).toHaveLength(4);
    expect(gray?.label).toBe("Cinza");
    expect(gray?.colors).toHaveLength(4);
    expect(applyChartColorPalette(red!, mergeComunicadoChartOptions({})).seriesColor).toBe(
      red!.seriesColor,
    );
    expect(applyChartColorPalette(gray!, mergeComunicadoChartOptions({})).categoryColors).toEqual(
      gray!.colors,
    );
  });

  it("inclui 4 escalas semânticas com 5 stops", () => {
    for (const id of CHART_SEMANTIC_PALETTE_IDS) {
      const palette = CHART_COLOR_PALETTES.find((item) => item.id === id);
      expect(palette, id).toBeTruthy();
      expect(palette!.kind).toBe("semantic");
      expect(palette!.colors).toHaveLength(5);
      const next = applyChartColorPalette(palette!, mergeComunicadoChartOptions({}));
      expect(next.categoryColors).toEqual(palette!.colors);
      expect(next.colorScale?.paletteId).toBe(id);
    }
    expect(chartPalettesByKind("semantic")).toHaveLength(4);
  });

  it("applyChartColorScaleMode by_value aplica rampa rag-good-first por padrão", () => {
    const next = applyChartColorScaleMode(mergeComunicadoChartOptions({}), "by_value");
    expect(next.colorScale?.mode).toBe("by_value");
    expect(next.colorScale?.polarity).toBe("high_is_bad");
    expect(next.colorScale?.paletteId).toBe("rag-good-first");
    expect(next.categoryColors).toHaveLength(5);
  });

  it("applyChartColorScaleMode by_goal grava mode sem exigir paleta", () => {
    const next = applyChartColorScaleMode(
      mergeComunicadoChartOptions({}),
      "by_goal",
      "high_is_good",
    );
    expect(next.colorScale?.mode).toBe("by_goal");
    expect(next.colorScale?.polarity).toBe("high_is_good");
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
