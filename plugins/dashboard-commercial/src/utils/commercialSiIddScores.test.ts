import { describe, expect, it } from "vitest";

import { COMMERCIAL_SI_INDICATOR_IDS } from "../constants/commercialIndicators";

describe("commercial SI indicator ids", () => {
  it("alinha ao catálogo SI ativo", () => {
    expect(COMMERCIAL_SI_INDICATOR_IDS.rol).toBe("commercial-rol");
    expect(COMMERCIAL_SI_INDICATOR_IDS.closingRate).toBe(
      "commercial-closing-rate",
    );
    expect(COMMERCIAL_SI_INDICATOR_IDS.newBusinessRol).toBe(
      "commercial-new-business-rol-pct",
    );
  });
});
