import { describe, expect, it } from "vitest";

import { resolveKpiComparisonTone } from "./kpiComparisonTone";

describe("resolveKpiComparisonTone", () => {
  it("marca verde quando ROL está acima da meta", () => {
    expect(
      resolveKpiComparisonTone(
        { available: true, error: null, value: 100, target: 80 },
        "higher_is_better",
      ),
    ).toBe("positive");
  });

  it("marca vermelho quando ROL está abaixo da meta", () => {
    expect(
      resolveKpiComparisonTone(
        { available: true, error: null, value: 13_545.2, target: 50_000 },
        "higher_is_better",
      ),
    ).toBe("negative");
  });

  it("marca verde quando custo fixo está abaixo da meta", () => {
    expect(
      resolveKpiComparisonTone(
        { available: true, error: null, value: 10, target: 12 },
        "lower_is_better",
      ),
    ).toBe("positive");
  });

  it("retorna undefined sem meta ou valor", () => {
    expect(
      resolveKpiComparisonTone(
        { available: true, error: null, value: 10, target: undefined },
        "higher_is_better",
      ),
    ).toBeUndefined();
  });
});
