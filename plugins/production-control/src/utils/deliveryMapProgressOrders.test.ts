import { describe, expect, it } from "vitest";

import type { DeliveryMapSection } from "../types";
import {
  collectDeliveryMapProgressOrderBatches,
  DELIVERY_MAP_OVERDUE_SECTION_KEY,
  isDeliveryMapSectionEligibleForProgress,
} from "./deliveryMapProgressOrders";

function section(
  sectionKey: string,
  rows: Array<{ production_order: string }>,
  dueDate: string | null = "2026-08-24",
): DeliveryMapSection {
  return {
    section_key: sectionKey,
    label: sectionKey,
    due_date: dueDate,
    row_count: rows.length,
    rows: rows.map((row) => ({
      production_order: row.production_order,
      product_code: "90262910",
      product_description: null,
      due_date: dueDate,
      planned_qty: 1,
      produced_qty: 0,
      pending_qty: 1,
      observation: null,
      days_late: 0,
      is_delayed: false,
      mp_ok: false,
      work_center: "",
      is_reported: false,
    })),
  };
}

describe("isDeliveryMapSectionEligibleForProgress", () => {
  it("inclui hoje+atrasadas e até 5 dias à frente", () => {
    expect(
      isDeliveryMapSectionEligibleForProgress(
        section(DELIVERY_MAP_OVERDUE_SECTION_KEY, [{ production_order: "1" }], null),
      ),
    ).toBe(true);

    const today = new Date();
    const inThreeDays = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 3)
      .toISOString()
      .slice(0, 10);
    const inTenDays = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 10)
      .toISOString()
      .slice(0, 10);

    expect(
      isDeliveryMapSectionEligibleForProgress(
        section("2026-future", [{ production_order: "2" }], inThreeDays),
      ),
    ).toBe(true);
    expect(
      isDeliveryMapSectionEligibleForProgress(
        section("2026-far", [{ production_order: "3" }], inTenDays),
      ),
    ).toBe(false);
  });
});

describe("collectDeliveryMapProgressOrderBatches", () => {
  it("prioriza hoje+atrasadas e separa demais elegíveis", () => {
    const today = new Date();
    const inTwoDays = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 2)
      .toISOString()
      .slice(0, 10);
    const inTenDays = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 10)
      .toISOString()
      .slice(0, 10);

    const batches = collectDeliveryMapProgressOrderBatches({
      branch: "01",
      sections: [
        section(DELIVERY_MAP_OVERDUE_SECTION_KEY, [{ production_order: "OP-A" }], null),
        section("future", [{ production_order: "OP-B" }], inTwoDays),
        section("far", [{ production_order: "OP-C" }], inTenDays),
      ],
      summary: { order_count: 3, section_count: 3 },
      filters: { search: "" },
      snapshot: { refreshed_at: null, refreshed_by: null, horizon_end: null, seeded: false },
    });

    expect(batches.priority).toEqual(["OP-A"]);
    expect(batches.deferred).toEqual(["OP-B"]);
  });
});
