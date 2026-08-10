import { describe, expect, it } from "vitest";

import { hasCustomerEnrichmentCoverage } from "./customerEnrichmentCoverage";

describe("hasCustomerEnrichmentCoverage", () => {
  it("considera coberta a resposta atual e o enrichment válido preservado", () => {
    expect(
      hasCustomerEnrichmentCoverage({
        coverageKnown: true,
        enrichmentAvailable: false,
      }),
    ).toBe(true);
    expect(
      hasCustomerEnrichmentCoverage({
        coverageKnown: false,
        enrichmentAvailable: true,
      }),
    ).toBe(true);
  });

  it("não confunde ausência de cobertura com valor vazio", () => {
    expect(
      hasCustomerEnrichmentCoverage({
        coverageKnown: false,
        enrichmentAvailable: false,
      }),
    ).toBe(false);
    expect(hasCustomerEnrichmentCoverage({})).toBe(false);
  });
});
