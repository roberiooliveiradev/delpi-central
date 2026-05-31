import { describe, expect, it } from "vitest";

import { buildSecuritySummaryView } from "./securitySummary";

describe("buildSecuritySummaryView", () => {
  it("formata contagens do resumo de segurança", () => {
    expect(
      buildSecuritySummaryView({
        windowHours: 24,
        since: "2026-01-01",
        blockedCount: 2,
        flaggedCount: 5,
        scannedCount: 1,
        totalEvents: 8,
        flagDistribution: [],
      }),
    ).toEqual({
      blocked: "2",
      flagged: "5",
      scanned: "1",
      totalEvents: "8",
    });
  });
});
