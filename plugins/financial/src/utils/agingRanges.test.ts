import { describe, expect, it } from "vitest";

import { estimateAverageDaysLateFromAging, sortAgingByOrder } from "./agingRanges";

describe("sortAgingByOrder", () => {
  it("puts on-time before late ranges even when the payload arrives shuffled", () => {
    const sorted = sortAgingByOrder([
      { code: "ATRASO_ACIMA_30_DIAS", order: 5 },
      { code: "EM_DIA", order: 1 },
      { code: "ATRASO_1_A_5_DIAS", order: 2 },
    ]);
    expect(sorted.map((item) => item.code)).toEqual([
      "EM_DIA",
      "ATRASO_1_A_5_DIAS",
      "ATRASO_ACIMA_30_DIAS",
    ]);
  });
});

describe("estimateAverageDaysLateFromAging", () => {
  it("weights only late buckets", () => {
    const average = estimateAverageDaysLateFromAging([
      { code: "EM_DIA", count: 100 },
      { code: "ATRASO_1_A_5_DIAS", count: 10 },
      { code: "ATRASO_16_A_30_DIAS", count: 10 },
    ]);
    expect(average).toBeCloseTo((10 * 3 + 10 * 23) / 20);
  });
});
