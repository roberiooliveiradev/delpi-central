import { describe, expect, it } from "vitest";

import { computeSimulateSummary } from "./simulateSummary";

describe("computeSimulateSummary", () => {
  it("normaliza contagens negativas", () => {
    expect(computeSimulateSummary(-1, -2, false)).toEqual({
      agentCount: 0,
      sessionCount: 0,
      hasResult: false,
    });
  });

  it("marca resultado quando simulação concluiu", () => {
    expect(computeSimulateSummary(3, 12, true)).toEqual({
      agentCount: 3,
      sessionCount: 12,
      hasResult: true,
    });
  });
});
