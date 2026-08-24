import { describe, expect, it } from "vitest";

import type { MaterialsLine } from "../types";
import { buildFinishedProductShortageExcelPayload, buildMaterialsExcelPayload } from "./materialsExcel";

const LINE: MaterialsLine = {
  id: "SC001/01",
  request_number: "SC001",
  request_item: "01",
  product_code: "10020113",
  product_description: "Cobre",
  unit: "KG",
  warehouse: "01",
  supplier_name: "Fornecedor",
  open_quantity: 50,
  required_date: "2026-08-20",
  issue_date: "2026-08-01",
  available_stock: 80,
  open_purchase_order_quantity: 20,
  open_commitment_quantity: 10,
  projected_balance: 90,
  needed_from_sc1: 0,
  safety_stock: 0,
};

describe("buildMaterialsExcelPayload", () => {
  it("exports the visible page without financial fields", () => {
    const payload = buildMaterialsExcelPayload([LINE]);
    expect(payload.rows).toHaveLength(1);
    expect(payload.rows[0]?.request).toBe("SC001/01");
    expect(payload.rows[0]?.product).toBe("10020113");
    expect(payload.rows[0]?.open).toBe(50);
    expect(JSON.stringify(payload)).not.toMatch(/preco|valor|price|value/i);
  });

  it("keeps an empty payload honest", () => {
    expect(buildMaterialsExcelPayload([]).rows).toEqual([]);
  });

  it("exports visible sets with their raw materials", () => {
    const payload = buildFinishedProductShortageExcelPayload([
      {
        production_order: "24608101001",
        planned_start_date: "2026-09-12",
        due_date: "2026-09-20",
        status: "shortage",
        materials: [
          {
            product_code: "10080001",
            product_description: "Cabo",
            unit: "KG",
            status: "shortage",
            shortage_date: "2026-09-12",
            shortage_quantity: 12,
            needed_quantity: 12,
            consuming_production_order: "24608101003",
          },
        ],
      },
    ]);
    expect(payload.rows).toHaveLength(1);
    expect(payload.rows[0]?.set).toBe("24608101001");
    expect(payload.rows[0]?.mp).toContain("10080001");
    expect(payload.rows[0]?.deficit).toBe(12);
  });
});
