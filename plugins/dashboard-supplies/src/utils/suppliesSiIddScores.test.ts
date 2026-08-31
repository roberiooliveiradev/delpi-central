import { describe, expect, it } from "vitest";

import { SUPPLIES_SI_INDICATORS } from "../constants/siIndicatorIds";

describe("supplies SI indicator ids", () => {
  it("expõe indicator_id canônicos do catálogo SI", () => {
    expect(SUPPLIES_SI_INDICATORS.cpv).toBe("supplies-cpv");
    expect(SUPPLIES_SI_INDICATORS.otd).toBe("supplies-otd");
    expect(SUPPLIES_SI_INDICATORS.stockTurnover).toBe(
      "supplies-stock-turnover",
    );
    expect(SUPPLIES_SI_INDICATORS.stockValue).toBe("supplies-stock-value");
    expect(SUPPLIES_SI_INDICATORS.negotiationSavings).toBe(
      "supplies-negotiation-savings",
    );
  });
});
