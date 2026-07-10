import { describe, expect, it } from "vitest";

import { usableSeriesChartPoints } from "./comunicadoChartOptions";

describe("usableSeriesChartPoints", () => {
  it("ignora pontos sem valor numérico", () => {
    const filtered = usableSeriesChartPoints([
      { label: "A", value: 10 },
      { label: "B", value: null },
      { label: "C", value: undefined },
      { label: "D", value: Number.NaN },
      { label: "E", value: 20 },
    ]);
    expect(filtered).toHaveLength(2);
    expect(filtered[0].label).toBe("A");
    expect(filtered[1].label).toBe("E");
  });
});
