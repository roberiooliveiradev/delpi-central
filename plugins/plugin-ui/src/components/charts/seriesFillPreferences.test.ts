import { describe, expect, it } from "vitest";

import {
  applySeriesFillPreferences,
  applySeriesViewPreferences,
  resetSeriesViewPreferences,
} from "./seriesFillPreferences";
import type { MultiTypeSeriesSpec } from "./MultiTypeSeriesChart";

const BASE: MultiTypeSeriesSpec[] = [
  {
    dataKey: "rol_matrix",
    name: "Matriz",
    fill: "var(--chart-1)",
    trendSource: true,
  },
  {
    dataKey: "rol_branch",
    name: "Filial",
    fill: "var(--chart-2)",
    trendSource: true,
  },
  {
    dataKey: "rol_matrix_prior",
    name: "Matriz (ano ant.)",
    fill: "var(--chart-3)",
  },
];

describe("applySeriesFillPreferences", () => {
  it("mantém defaults quando não há overrides", () => {
    expect(applySeriesFillPreferences(BASE)).toEqual(BASE);
    expect(applySeriesFillPreferences(BASE, null)).toEqual(BASE);
    expect(applySeriesFillPreferences(BASE, {})).toEqual(BASE);
  });

  it("aplica override por dataKey e preserva demais campos", () => {
    const next = applySeriesFillPreferences(BASE, {
      rol_matrix: "#ff0000",
      unknown: "#000",
    });
    expect(next[0]).toEqual({
      dataKey: "rol_matrix",
      name: "Matriz",
      fill: "#ff0000",
      trendSource: true,
    });
    expect(next[1].fill).toBe("var(--chart-2)");
    expect(next[2].fill).toBe("var(--chart-3)");
  });

  it("preserva axis e plotAs ao aplicar cor", () => {
    const dual: MultiTypeSeriesSpec[] = [
      {
        dataKey: "faturamento",
        name: "Faturamento",
        fill: "var(--chart-1)",
      },
      {
        dataKey: "quantidade",
        name: "Quantidade",
        fill: "var(--chart-2)",
        axis: "secondary",
        plotAs: "line",
      },
    ];
    const next = applySeriesFillPreferences(dual, { quantidade: "#ea580c" });
    expect(next[1]).toMatchObject({
      dataKey: "quantidade",
      fill: "#ea580c",
      axis: "secondary",
      plotAs: "line",
    });
  });

  it("ignora override vazio e não muta o array original", () => {
    const original = BASE.map((entry) => ({ ...entry }));
    const next = applySeriesFillPreferences(original, {
      rol_branch: "   ",
      rol_matrix_prior: "#64748b",
    });
    expect(next[1].fill).toBe("var(--chart-2)");
    expect(next[2].fill).toBe("#64748b");
    expect(original[2].fill).toBe("var(--chart-3)");
  });
});

describe("applySeriesViewPreferences", () => {
  it("sem overrides visuais preserva cores e aplica tendência só pelo flag global", () => {
    const next = applySeriesViewPreferences(BASE, { showTrend: true });
    expect(next.map((entry) => entry.dataKey)).toEqual([
      "rol_matrix",
      "rol_branch",
      "rol_matrix_prior",
    ]);
    expect(next[0]).toMatchObject({
      dataKey: "rol_matrix",
      fill: "var(--chart-1)",
      trendSource: true,
    });
    expect(next[1].trendSource).toBe(true);
    expect(next[2]).toMatchObject({
      dataKey: "rol_matrix_prior",
      fill: "var(--chart-3)",
      trendSource: false,
    });
  });

  it("oculta por dataKey sem mutar origem e aplica tendência independente", () => {
    const original = BASE.map((entry) => ({ ...entry }));
    const next = applySeriesViewPreferences(BASE, {
      showTrend: true,
      hiddenSeries: { rol_branch: true },
      seriesTrend: { rol_matrix: false, rol_matrix_prior: true },
      seriesFills: { rol_matrix: "#ff0000" },
    });
    expect(next.map((entry) => entry.dataKey)).toEqual(["rol_matrix", "rol_matrix_prior"]);
    expect(next[0]).toMatchObject({
      dataKey: "rol_matrix",
      fill: "#ff0000",
      trendSource: false,
    });
    expect(next[1].trendSource).toBe(false);
    expect(original).toEqual(BASE);
  });

  it("duas séries elegíveis podem ter tendência ligada/desligada à parte do global", () => {
    const next = applySeriesViewPreferences(BASE, {
      showTrend: false,
      seriesTrend: { rol_matrix: true, rol_branch: true },
    });
    expect(next[0].trendSource).toBe(true);
    expect(next[1].trendSource).toBe(true);
    expect(next[2].trendSource).toBe(false);
  });

  it("reset da série remove só aquele dataKey", () => {
    const prev = {
      chartType: "column" as const,
      seriesFills: { rol_matrix: "#f00", rol_branch: "#0f0" },
      hiddenSeries: { rol_matrix: true },
      seriesTrend: { rol_matrix: true, rol_branch: false },
    };
    const next = resetSeriesViewPreferences(prev, "rol_matrix");
    expect(next.seriesFills).toEqual({ rol_branch: "#0f0" });
    expect(next.hiddenSeries).toBeUndefined();
    expect(next.seriesTrend).toEqual({ rol_branch: false });
  });
});
