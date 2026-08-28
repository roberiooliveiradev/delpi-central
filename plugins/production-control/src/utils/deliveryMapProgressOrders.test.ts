import { describe, expect, it } from "vitest";

import type { DeliveryMapSection } from "../types";
import {
  collectDeliveryMapProgressOrderBatches,
  DELIVERY_MAP_OVERDUE_SECTION_KEY,
  DELIVERY_MAP_PROGRESS_MAX_SECTIONS,
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
  it("inclui só as N primeiras seções da grade", () => {
    const overdue = section(DELIVERY_MAP_OVERDUE_SECTION_KEY, [{ production_order: "1" }], null);
    expect(isDeliveryMapSectionEligibleForProgress(overdue, 0)).toBe(true);
    expect(isDeliveryMapSectionEligibleForProgress(overdue, 2)).toBe(true);
    expect(isDeliveryMapSectionEligibleForProgress(overdue, 3)).toBe(false);
    expect(DELIVERY_MAP_PROGRESS_MAX_SECTIONS).toBe(3);
  });
});

describe("collectDeliveryMapProgressOrderBatches", () => {
  it("prioriza a 1ª tabela e limita às 3 primeiras", () => {
    const batches = collectDeliveryMapProgressOrderBatches({
      branch: "01",
      sections: [
        section(DELIVERY_MAP_OVERDUE_SECTION_KEY, [{ production_order: "OP-A" }], null),
        section("d1", [{ production_order: "OP-B" }], "2026-08-25"),
        section("d2", [{ production_order: "OP-C" }], "2026-08-26"),
        section("d3", [{ production_order: "OP-D" }], "2026-08-27"),
      ],
      summary: { order_count: 4, section_count: 4 },
      filters: { search: "" },
      snapshot: { refreshed_at: null, refreshed_by: null, horizon_end: null, seeded: false },
    });

    expect(batches.priority).toEqual(["OP-A"]);
    expect(batches.deferred).toEqual(["OP-B", "OP-C"]);
    expect(batches.deferred).not.toContain("OP-D");
  });
});
