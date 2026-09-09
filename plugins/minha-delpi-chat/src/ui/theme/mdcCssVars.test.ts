import { describe, expect, it } from "vitest";

import {
  resolveChartSeriesColor,
  resolveChartSeriesColors,
  resolveMermaidTheme,
  resolvePaletteFamilyColors,
} from "./mdcCssVars";

describe("resolveMermaidTheme", () => {
  it("usa tema claro no modo light", () => {
    expect(resolveMermaidTheme(false)).toBe("default");
  });

  it("usa tema escuro no modo dark", () => {
    expect(resolveMermaidTheme(true)).toBe("dark");
  });
});

describe("resolveChartSeriesColors", () => {
  it("prioriza cores explícitas da API", () => {
    expect(resolveChartSeriesColors(["#10b981", ""], false)).toEqual(["#10b981"]);
  });

  it("ignora array vazio e usa fallback saturado no modo claro", () => {
    const colors = resolveChartSeriesColors([], false);

    expect(colors.length).toBeGreaterThan(0);
    expect(colors[0]).toBe("#0478b5");
  });

  it("usa fallback mais claro no modo escuro", () => {
    const colors = resolveChartSeriesColors(undefined, true);

    expect(colors[0]).toBe("#38bdf8");
  });

  it("usa paletteFamily quando colors[] está vazio", () => {
    expect(resolveChartSeriesColors([], false, "warm")).toEqual([
      "var(--mdc-chart-series-4)",
      "var(--mdc-chart-series-5)",
    ]);
  });
});

describe("resolvePaletteFamilyColors", () => {
  it("delega ao Color Family Catalog do plugin-ui", () => {
    expect(resolvePaletteFamilyColors("brand")).toEqual([
      "var(--mdc-chart-series-1)",
      "var(--mdc-chart-series-10)",
    ]);
    expect(resolvePaletteFamilyColors("sequential-blue")).toEqual([
      "var(--mdc-heatmap-low)",
      "var(--mdc-heatmap-high)",
    ]);
  });

  it("alinha status e diverging-status", () => {
    expect(resolvePaletteFamilyColors("status")).toEqual(
      resolvePaletteFamilyColors("diverging-status"),
    );
  });

  it("retorna vazio para família desconhecida", () => {
    expect(resolvePaletteFamilyColors("unknown-family")).toEqual([]);
  });
});

describe("resolveChartSeriesColor", () => {
  it("nunca retorna string vazia", () => {
    expect(resolveChartSeriesColor([], 0, false)).toBe("#0478b5");
    expect(resolveChartSeriesColor([], 2, true)).toBe("#4ade80");
  });
});
