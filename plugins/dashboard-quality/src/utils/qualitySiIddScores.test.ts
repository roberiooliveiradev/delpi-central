import { describe, expect, it } from "vitest";

import { QUALITY_SI_INDICATORS } from "../constants/siIndicatorIds";

describe("quality SI indicator ids", () => {
  it("expõe indicator_id canônicos do catálogo SI", () => {
    expect(QUALITY_SI_INDICATORS.ppmInternal).toBe("quality-ppm-internal");
    expect(QUALITY_SI_INDICATORS.ppmExternal).toBe("quality-ppm-external");
    expect(QUALITY_SI_INDICATORS.kaizenIdeas).toBe("quality-kaizen-ideas");
    expect(QUALITY_SI_INDICATORS.kaizenFinancial).toBe(
      "quality-kaizen-financial",
    );
    expect(QUALITY_SI_INDICATORS.audit5s).toBe("quality-audit-5s");
    expect(QUALITY_SI_INDICATORS.scrapCostPct).toBe("quality-scrap-cost-pct");
    expect(QUALITY_SI_INDICATORS.reworkCostPct).toBe("quality-rework-cost-pct");
  });
});
