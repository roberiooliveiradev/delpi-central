import { describe, expect, it } from "vitest";

import { hasActivePurchaseOrdersFilters } from "./hasActiveFilters";
import { createDefaultQuery } from "./query";

describe("hasActivePurchaseOrdersFilters", () => {
  it("ignores all authorized units alone", () => {
    expect(hasActivePurchaseOrdersFilters(createDefaultQuery(["01", "02"]), ["01", "02"])).toBe(
      false,
    );
  });

  it("detects subset of units, text, dates and late_only", () => {
    expect(
      hasActivePurchaseOrdersFilters(
        { ...createDefaultQuery(["01"]), branches: ["01"] },
        ["01", "02"],
      ),
    ).toBe(true);
    expect(
      hasActivePurchaseOrdersFilters({
        ...createDefaultQuery(["01"]),
        order_number: "100",
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseOrdersFilters({
        ...createDefaultQuery(["01"]),
        late_only: true,
      }),
    ).toBe(true);
    expect(
      hasActivePurchaseOrdersFilters({
        ...createDefaultQuery(["01"]),
        expected_delivery_from: "2026-01-01",
      }),
    ).toBe(true);
  });
});
