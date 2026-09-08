import { describe, expect, it } from "vitest";

import { applySeriesFillPreferences } from "./seriesFillPreferences";
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
