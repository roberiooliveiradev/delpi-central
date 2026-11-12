import { describe, expect, it } from "vitest";

import {
  compactFiniteSeriesChartPoints,
  usableSeriesChartPoints,
} from "@delpi/plugin-ui/index";

describe("usableSeriesChartPoints", () => {
  it("preserva categorias com lacuna e reindexa densamente", () => {
    const input = [
      { label: "A", value: 10 },
      { label: "B", value: null },
      { label: "C", value: undefined },
      { label: "D", value: Number.NaN },
      { label: "E", value: 20 },
    ];
    const normalized = usableSeriesChartPoints(input);
    expect(normalized).toHaveLength(5);
    expect(normalized.map((point) => point.label)).toEqual(["A", "B", "C", "D", "E"]);
    expect(normalized.map((point) => point.sourceIndex)).toEqual([0, 1, 2, 3, 4]);
    expect(input).toHaveLength(5);
  });

  it("compactFinite remove só o ponto completo para pizza/funil", () => {
    const compacted = compactFiniteSeriesChartPoints([
      { label: "A", value: 10 },
      { label: "B", value: null },
      { label: "C", value: undefined },
      { label: "D", value: Number.NaN },
      { label: "E", value: 20 },
    ]);
    expect(compacted).toHaveLength(2);
    expect(compacted[0]?.label).toBe("A");
    expect(compacted[1]?.label).toBe("E");
    expect(compacted.map((point) => point.sourceIndex)).toEqual([0, 1]);
  });
});
