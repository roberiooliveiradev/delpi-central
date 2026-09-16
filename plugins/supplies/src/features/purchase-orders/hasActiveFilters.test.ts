import { describe, expect, it } from "vitest";

import { hasActivePurchaseOrdersFilters } from "./hasActiveFilters";
import { createDefaultQuery } from "./query";

describe("hasActivePurchaseOrdersFilters", () => {
  it("ignores Todas and full authorized scope alone", () => {
    expect(hasActivePurchaseOrdersFilters(createDefaultQuery(), ["01", "02"])).toBe(false);
    expect(
      hasActivePurchaseOrdersFilters(
        { ...createDefaultQuery(), branches: ["01", "02"] },
        ["01", "02"],
      ),
    ).toBe(false);
  });

  it("detects subset of units, text, dates and late_only", () => {
    expect(
      hasActivePurchaseOrdersFilters(
        { ...createDefaultQuery(), branches: ["01"] },
        ["01", "02"],
      ),
    ).toBe(true);
    expect(
      hasActivePurchaseOrdersFilters({
        ...createDefaultQuery(),
        order_number: "100",
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseOrdersFilters({
        ...createDefaultQuery(),
        late_only: true,
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseOrdersFilters({
        ...createDefaultQuery(),
        expected_delivery_from: "2026-01-01",
      }),
    ).toBe(true);
  });
});
