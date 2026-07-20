import { describe, expect, it } from "vitest";

import { projectionSituationParts } from "./projectionSituation";

describe("projectionSituationParts", () => {
  it("formata saldos e data de ruptura", () => {
    const parts = projectionSituationParts({
      as_of_date: "2026-07-17",
      initial_balance: 100,
      safety_stock: 80,
      eligible_purchase_quantity: 20,
      eligible_commitment_quantity: 30,
      final_projected_balance: 90,
      final_balance_after_safety: 10,
      minimum_projected_balance: -5,
      first_shortage_date: "2026-08-01",
      projected_remaining_to_buy: 5,
      status: "temporary_shortage",
      eligible_warehouses: ["01", "98", "99"],
      warnings: [],
    });

    expect(parts.initialBalance).toContain("100");
    expect(parts.shortageDate).toBe("01/08/2026");
    expect(parts.minimumBalance).toContain("5");
  });
});
