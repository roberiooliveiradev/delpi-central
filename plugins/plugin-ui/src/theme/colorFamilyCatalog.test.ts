import { describe, expect, it } from "vitest";

import {
  getColorFamilyDefinition,
  listColorFamilies,
  resolveColorFamily,
} from "./colorFamilyCatalog";

describe("colorFamilyCatalog", () => {
  it("lista famílias canônicas alinhadas à API", () => {
    expect(listColorFamilies()).toEqual([
      "brand",
      "sequential-blue",
      "cool",
      "warm",
      "diverging-status",
      "status",
      "categorical",
    ]);
  });

  it("resolve brand e sequential-blue para tokens MDC", () => {
    expect(resolveColorFamily("brand", "light")).toEqual([
      "var(--mdc-chart-series-1)",
      "var(--mdc-chart-series-10)",
    ]);
    expect(resolveColorFamily("sequential-blue", "dark")).toEqual([
      "var(--mdc-heatmap-low)",
      "var(--mdc-heatmap-high)",
    ]);
  });

  it("alinha status e diverging-status ao mesmo par semântico", () => {
    const diverging = resolveColorFamily("diverging-status");
    const status = resolveColorFamily("status");

    expect(status).toEqual(diverging);
    expect(status).toEqual([
      "var(--mdc-chart-series-5)",
      "var(--mdc-chart-series-3)",
    ]);
  });

  it("expõe categorical como série cíclica de tokens CSS", () => {
    const colors = resolveColorFamily("categorical");

    expect(colors).toHaveLength(10);
    expect(colors[0]).toBe("var(--mdc-chart-series-1)");
    expect(colors[9]).toBe("var(--mdc-chart-series-10)");
  });

  it("normaliza alias categorical-deck", () => {
    expect(resolveColorFamily("categorical-deck")).toEqual(resolveColorFamily("categorical"));
  });

  it("retorna vazio para família desconhecida ou ausente", () => {
    expect(resolveColorFamily(undefined)).toEqual([]);
    expect(resolveColorFamily("")).toEqual([]);
    expect(resolveColorFamily("neon-rainbow")).toEqual([]);
  });

  it("resolve cool e warm com tokens esperados", () => {
    expect(resolveColorFamily("cool")).toEqual([
      "var(--mdc-chart-series-7)",
      "var(--mdc-chart-series-2)",
    ]);
    expect(resolveColorFamily("warm")).toEqual([
      "var(--mdc-chart-series-4)",
      "var(--mdc-chart-series-5)",
    ]);
  });

  it("getColorFamilyDefinition retorna metadados da família", () => {
    const family = getColorFamilyDefinition("brand");
    expect(family?.id).toBe("brand");
    expect(family?.tokens.length).toBeGreaterThan(0);
  });
});
