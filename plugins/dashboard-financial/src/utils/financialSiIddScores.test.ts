import { describe, expect, it } from "vitest";

import { FINANCIAL_SI_INDICATORS } from "../constants/siIndicatorIds";

describe("financial SI indicator ids", () => {
  it("expõe indicator_id canônicos do catálogo SI", () => {
    expect(FINANCIAL_SI_INDICATORS.rol).toBe("commercial-rol");
    expect(FINANCIAL_SI_INDICATORS.ebitda).toBe("financial-ebitda");
    expect(FINANCIAL_SI_INDICATORS.fixedCost).toBe("financial-fixed-cost");
    expect(FINANCIAL_SI_INDICATORS.pmr).toBe("financial-pmr");
  });
});
