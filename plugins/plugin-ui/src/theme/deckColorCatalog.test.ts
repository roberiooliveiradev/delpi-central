import { describe, expect, it } from "vitest";

import { KPI_PART_FONT_SIZE_DEFAULTS } from "../components/layout/kpiCardParts";
import {
  DECK_CHART_DEFAULTS,
  DECK_COLOR_ACCENT,
  DECK_COLOR_SHAPE_STROKE,
  DECK_INPUT_DEFAULTS,
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

  it("define chrome visual padrão da tabela (raio, borda, sombra)", () => {
    expect(DECK_TABLE_DEFAULTS.borderRadius).toBe(16);
    expect(DECK_TABLE_DEFAULTS.borderWidth).toBe(1);
    expect(DECK_TABLE_DEFAULTS.frameStroke).toBe("#b4b4b4");
    expect(DECK_TABLE_DEFAULTS.boxShadow).toContain("rgba(15, 23, 42");
    expect(DECK_TABLE_DEFAULTS.borderRadius).toBe(DECK_KPI_DEFAULTS.borderRadius);
    expect(DECK_TABLE_DEFAULTS.boxShadow).toBe(DECK_KPI_DEFAULTS.boxShadow);
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
    expect(DECK_KPI_DEFAULTS.frame).toEqual({ x: 8, y: 34, w: 12, h: 10 });
  });

  it("frame inicial Full HD cabe título + valor sem clip vertical", () => {
    const slideH = 1080;
    const cardH = (DECK_KPI_DEFAULTS.frame.h / 100) * slideH;
    const padY = 10;
    const gap = 2;
    const titleH = KPI_PART_FONT_SIZE_DEFAULTS.title * 1.35;
    const valueH = KPI_PART_FONT_SIZE_DEFAULTS.value * 1.05;
    expect(cardH).toBeGreaterThanOrEqual(padY + titleH + gap + valueH);
  });

  it("define chrome do filtro: fundo branco, sombra e raio alinhados a KPI/gráfico", () => {
    expect(DECK_INPUT_DEFAULTS.backgroundColor).toBe(DECK_THEME_LIGHT.bg);
    expect(DECK_INPUT_DEFAULTS.borderColor).toBe("#b4b4b4");
    expect(DECK_INPUT_DEFAULTS.borderRadius).toBe(DECK_CHART_DEFAULTS.borderRadius);
    expect(DECK_INPUT_DEFAULTS.boxShadow).toBe(DECK_KPI_DEFAULTS.boxShadow);
    expect(DECK_INPUT_DEFAULTS.boxShadow).toBe(DECK_CHART_DEFAULTS.boxShadow);
    expect(DECK_INPUT_DEFAULTS.controlBorderColor).toBe(DECK_COLOR_SHAPE_STROKE);
    expect(DECK_INPUT_DEFAULTS.controlFill).toBe("#ffffff");
    expect(DECK_INPUT_DEFAULTS.frame).toEqual({ x: 8, y: 8, w: 12, h: 5 });
  });

  it("expõe CSS vars para herança no bloco de dados", () => {
    const vars = deckDataBlockCssVars();
    expect(vars["--tdp-data-accent"]).toBe(DECK_COLOR_ACCENT);
    expect(vars["--tdp-data-surface"]).toBe(DECK_THEME_LIGHT.bg);
  });
});
