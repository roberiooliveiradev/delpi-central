import { describe, expect, it } from "vitest";

import {
  buildEvaluationsSummaryView,
  formatEvaluationAverage,
  formatHelpfulRate,
} from "./evaluationsSummary";

describe("evaluationsSummary", () => {
  it("formata média e taxa útil", () => {
    expect(formatEvaluationAverage(4.25)).toBe("4.3");
    expect(formatHelpfulRate(0.67)).toBe("67%");
    expect(formatEvaluationAverage(null)).toBe("—");
  });

  it("monta view a partir do resumo da API", () => {
    expect(
      buildEvaluationsSummaryView({
        total: 12,
        averageScore: 3.5,
        helpfulRate: 0.5,
        distribution: [],
        recent24h: 2,
      }),
    ).toEqual({
      total: "12",
      averageScore: "3.5",
      helpfulRate: "50%",
      recent24h: "2",
    });
  });
});
