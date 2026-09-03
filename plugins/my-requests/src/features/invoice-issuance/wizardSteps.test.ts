import { describe, expect, it } from "vitest";

import { WIZARD_STEPS } from "./ui/InvoiceIssuanceWizard";

describe("invoice-issuance wizard", () => {
  it("expõe 6 etapas specialized", () => {
    expect(WIZARD_STEPS.map((s) => s.id)).toEqual([
      "recipient",
      "invoiceType",
      "items",
      "freight",
      "extras",
      "review",
    ]);
    expect(WIZARD_STEPS).toHaveLength(6);
  });
});
