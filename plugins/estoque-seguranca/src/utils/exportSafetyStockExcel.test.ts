import { describe, expect, it } from "vitest";

import type { SafetyStockItem } from "../types/safetyStock";
import {
  buildSafetyStockExportPayload,
  safetyStockItemToExportRow,
} from "./exportSafetyStockExcel";

function sampleItem(overrides: Partial<SafetyStockItem> = {}): SafetyStockItem {
  return {
    product_code: "10010005",
    product_description: "CABO",
    product_type: "MP",
    unit: "MT",
    product_group: "10",
    branch: "01",
    blocked: false,
    safety_stock: 100,
    primary_stock: 40,
    work_in_process_stock: 0,
    warehouse_50_stock: 0,
    warehouse_98_stock: 10,
    warehouse_99_stock: 5,
    work_in_process_committed: 0,
    work_in_process_available: 0,
    deficit_quantity: 45,
    status: "below_safety_stock",
    ...overrides,
  };
}

describe("exportSafetyStockExcel", () => {
  it("monta linha com saldo consolidado e situação em português", () => {
    const row = safetyStockItemToExportRow(sampleItem());
    expect(row.display_balance).toBe(55);
    expect(row.status).toContain("Abaixo");
    expect(row.blocked).toBe("Não");
  });

  it("monta payload com colunas esperadas", () => {
    const payload = buildSafetyStockExportPayload([sampleItem()]);
    expect(payload.columns.map((column) => column.key)).toContain("display_balance");
    expect(payload.rows).toHaveLength(1);
  });
});
