import { describe, expect, it } from "vitest";

import {
  DECK_CHART_DEFAULTS,
  DECK_COLOR_ACCENT,
  DECK_KPI_DEFAULTS,
  DECK_SHAPE_DEFAULTS,
  DECK_TABLE_DEFAULTS,
  DECK_THEME_LIGHT,
  OFFICE_CHART_SERIES_COLOR,
  deckDataBlockCssVars,
} from "./deckColorCatalog";

describe("deckColorCatalog", () => {
  it("alinha accent do gráfico, KPI e forma", () => {
    expect(DECK_COLOR_ACCENT).toBe("#089bdb");
    expect(OFFICE_CHART_SERIES_COLOR).toBe(DECK_COLOR_ACCENT);
    expect(DECK_CHART_DEFAULTS.seriesColor).toBe(DECK_COLOR_ACCENT);
    expect(DECK_SHAPE_DEFAULTS.fill).toBe(DECK_COLOR_ACCENT);
    expect(DECK_SHAPE_DEFAULTS.stroke).toBe("#000000");
    expect(DECK_SHAPE_DEFAULTS.lineStroke).toBe(DECK_COLOR_ACCENT);
    expect(DECK_KPI_DEFAULTS.accent).toBe(DECK_COLOR_ACCENT);
  });

  it("separa grade de células e contorno de moldura na tabela", () => {
    expect(DECK_TABLE_DEFAULTS.borderColor).toBe("#e2e8f0");
    expect(DECK_TABLE_DEFAULTS.frameStroke).toBe("#b4b4b4");
    expect(DECK_TABLE_DEFAULTS.frameFill).toBe(DECK_THEME_LIGHT.bg);
    expect(DECK_TABLE_DEFAULTS.frameStroke).not.toBe(DECK_TABLE_DEFAULTS.borderColor);
  });

  it("usa superfície clara no KPI e na tabela", () => {
    expect(DECK_KPI_DEFAULTS.backgroundColor).toBe(DECK_THEME_LIGHT.bg);
    expect(DECK_TABLE_DEFAULTS.cellBg).toBe(DECK_THEME_LIGHT.bg);
  });

  it("define chrome visual padrão do gráfico (raio, borda, sombra)", () => {
    expect(DECK_CHART_DEFAULTS.borderRadius).toBe(16);
    expect(DECK_CHART_DEFAULTS.borderColor).toBe("#b4b4b4");
    expect(DECK_CHART_DEFAULTS.borderWidth).toBe(1);
    expect(DECK_CHART_DEFAULTS.boxShadow).toContain("rgba(15, 23, 42");
  });

  it("define chrome visual padrão do KPI (raio, borda, sombra, ícone)", () => {
    expect(DECK_KPI_DEFAULTS.borderRadius).toBe(16);
    expect(DECK_KPI_DEFAULTS.borderColor).toBe("#b4b4b4");
    expect(DECK_KPI_DEFAULTS.borderWidth).toBe(1);
    expect(DECK_KPI_DEFAULTS.boxShadow).toContain("rgba(15, 23, 42");
    expect(DECK_KPI_DEFAULTS.iconName).toBe("Gauge");
  });

  it("expõe CSS vars para herança no bloco de dados", () => {
    const vars = deckDataBlockCssVars();
    expect(vars["--tdp-data-accent"]).toBe(DECK_COLOR_ACCENT);
    expect(vars["--tdp-data-surface"]).toBe(DECK_THEME_LIGHT.bg);
  });
});
