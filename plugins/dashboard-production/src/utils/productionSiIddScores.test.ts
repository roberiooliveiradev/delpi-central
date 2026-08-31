import { describe, expect, it } from "vitest";

import { PRODUCTION_SI_INDICATORS } from "../constants/siIndicatorIds";

describe("production SI indicator ids", () => {
  it("expõe indicator_id canônicos do catálogo SI", () => {
    expect(PRODUCTION_SI_INDICATORS.directLabor).toBe("production-direct-labor");
    expect(PRODUCTION_SI_INDICATORS.productionCosts).toBe("production-costs");
    expect(PRODUCTION_SI_INDICATORS.depreciation).toBe("production-depreciation");
    expect(PRODUCTION_SI_INDICATORS.oee).toBe("production-oee");
    expect(PRODUCTION_SI_INDICATORS.otd).toBe("production-otd");
  });
});
