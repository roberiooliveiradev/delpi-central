import { describe, expect, it } from "vitest";

import { hasActivePurchaseRequestsFilters } from "./hasActiveFilters";
import { createDefaultQuery } from "./query";

describe("hasActivePurchaseRequestsFilters", () => {
  it("ignores Todas and baseline period", () => {
    expect(hasActivePurchaseRequestsFilters(createDefaultQuery())).toBe(false);
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(),
        branches: ["01", "02"],
      }),
    ).toBe(false);
  });

  it("detects text, stage and custom period", () => {
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(),
        request_number: "SC1",
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(),
        overall_stages: ["awaiting_order"],
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(),
        date_from: "2020-01-01",
      }),
    ).toBe(true);
  });
});
