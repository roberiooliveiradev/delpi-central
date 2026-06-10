import { describe, expect, it } from "vitest";

import {
  resolveChartSeriesColor,
  resolveChartSeriesColors,
  resolveMermaidTheme,
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
});

describe("resolveChartSeriesColor", () => {
  it("nunca retorna string vazia", () => {
    expect(resolveChartSeriesColor([], 0, false)).toBe("#0478b5");
    expect(resolveChartSeriesColor([], 2, true)).toBe("#4ade80");
  });
});
