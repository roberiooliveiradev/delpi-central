import { describe, expect, it } from "vitest";

import {
  asMaterialsSetStatus,
  asMaterialsWorkspace,
  canQueryFinishedProductShortages,
  deliveryMapOrderHref,
  finishedProductShortageQueryCode,
  countSetMaterialsByStatus,
  filterSetMaterials,
  machineLoadLocateHref,
  safetyStockHref,
  sortSetMaterials,
  uniqueMaterialAvailability,
} from "./finishedProductShortageQuery";

describe("finishedProductShortageQuery", () => {
  it("keeps pa-shortage as its own workspace", () => {
    expect(asMaterialsWorkspace("pa-shortage")).toBe("pa-shortage");
    expect(asMaterialsWorkspace("shortage")).toBe("shortage");
    expect(asMaterialsWorkspace(null)).toBe("excess");
  });

  it("does not treat an empty or short code as a fetchable query", () => {
    expect(canQueryFinishedProductShortages("")).toBe(false);
    expect(canQueryFinishedProductShortages("9026")).toBe(false);
    expect(canQueryFinishedProductShortages("90263114")).toBe(true);
  });

  it("only the consult workspace with a valid PA starts a fetch", () => {
    expect(finishedProductShortageQueryCode("pa-shortage", null)).toBe("");
    expect(finishedProductShortageQueryCode("pa-shortage", "9026")).toBe("");
    expect(finishedProductShortageQueryCode("excess", "90263114")).toBe("");
    expect(finishedProductShortageQueryCode("pa-shortage", "90263114")).toBe("90263114");
  });

  it("builds PCP shortcuts from the mother order", () => {
    expect(machineLoadLocateHref("01", "10868901001")).toBe(
      "/apps/production-control/machine-load?branch=01&locate=10868901001",
    );
    expect(deliveryMapOrderHref("02", "10868901001")).toBe(
      "/apps/production-control/delivery-map?branch=02&q=10868901001",
    );
  });

  it("accepts only the BFF set statuses", () => {
    expect(asMaterialsSetStatus("shortage")).toBe("shortage");
    expect(asMaterialsSetStatus("urgente")).toBe("all");
  });

  it("builds the satellite safety-stock link from the MP code", () => {
    expect(safetyStockHref("10080001")).toBe("/apps/estoque-seguranca?q=10080001");
  });

  it("lists shortage materials before covered ones", () => {
    const sorted = sortSetMaterials([
      { product_code: "10500233", product_description: "Ok", unit: "UN", status: "ok", shortage_date: null, shortage_quantity: 0, consuming_production_order: "" },
      { product_code: "10080003", product_description: "Falta", unit: "UN", status: "shortage", shortage_date: "2026-09-21", shortage_quantity: 12, consuming_production_order: "24749901003" },
    ]);
    expect(sorted.map((item) => item.product_code)).toEqual(["10080003", "10500233"]);
  });

  it("counts and filters materials for the set tabs", () => {
    const materials = [
      { product_code: "10500233", product_description: "Ok", unit: "UN", status: "ok" as const, shortage_date: null, shortage_quantity: 0, consuming_production_order: "" },
      { product_code: "10080003", product_description: "Falta", unit: "UN", status: "shortage" as const, shortage_date: "2026-09-21", shortage_quantity: 12, consuming_production_order: "24749901003" },
    ];
    expect(countSetMaterialsByStatus(materials)).toEqual({
      all: 2,
      shortage: 1,
      no_commitment: 0,
      ok: 1,
    });
    expect(filterSetMaterials(materials, "ok").map((item) => item.product_code)).toEqual([
      "10500233",
    ]);
  });

  it("computes availability from the worst status of each unique MP", () => {
    expect(
      uniqueMaterialAvailability([
        {
          production_order: "24749901001",
          planned_start_date: "2026-09-21",
          due_date: "2026-09-21",
          status: "shortage",
          materials: [
            { product_code: "A", product_description: "", unit: "PC", status: "shortage", shortage_date: "2026-09-21", shortage_quantity: 1, consuming_production_order: "" },
            { product_code: "B", product_description: "", unit: "PC", status: "ok", shortage_date: null, shortage_quantity: 0, consuming_production_order: "" },
            { product_code: "C", product_description: "", unit: "PC", status: "shortage", shortage_date: "2026-09-21", shortage_quantity: 1, consuming_production_order: "" },
          ],
        },
      ]),
    ).toEqual({ ok: 1, total: 3, percent: 33 });
  });
});
