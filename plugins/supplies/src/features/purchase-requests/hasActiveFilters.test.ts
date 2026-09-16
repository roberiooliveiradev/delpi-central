import { describe, expect, it } from "vitest";

import { hasActivePurchaseRequestsFilters } from "./hasActiveFilters";
import { createDefaultQuery } from "./query";

describe("hasActivePurchaseRequestsFilters", () => {
  it("ignores default branch and baseline period", () => {
    expect(hasActivePurchaseRequestsFilters(createDefaultQuery(["01"]))).toBe(false);
  });

  it("detects text, stage and custom period", () => {
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(["01"]),
        request_number: "SC1",
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(["01"]),
        overall_stages: ["awaiting_order"],
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseRequestsFilters({
        ...createDefaultQuery(["01"]),
        date_from: "2020-01-01",
      }),
    ).toBe(true);
  });
});
