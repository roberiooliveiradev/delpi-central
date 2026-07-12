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
    expect(DECK_KPI_DEFAULTS.accent).toBe(DECK_COLOR_ACCENT);
  });

  it("usa superfície clara no KPI e na tabela", () => {
    expect(DECK_KPI_DEFAULTS.backgroundColor).toBe(DECK_THEME_LIGHT.bg);
    expect(DECK_TABLE_DEFAULTS.cellBg).toBe(DECK_THEME_LIGHT.bg);
  });

  it("expõe CSS vars para herança no bloco de dados", () => {
    const vars = deckDataBlockCssVars();
    expect(vars["--tdp-data-accent"]).toBe(DECK_COLOR_ACCENT);
    expect(vars["--tdp-data-surface"]).toBe(DECK_THEME_LIGHT.bg);
  });
});
