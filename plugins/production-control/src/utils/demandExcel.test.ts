import { describe, expect, it } from "vitest";

import type { DemandLine } from "../types";
import { buildDemandExcelPayload } from "./demandExcel";

function line(overrides: Partial<DemandLine> = {}): DemandLine {
  return {
    id: "01|045123|01",
    branch: "01",
    sales_order: "045123",
    line_item: "01",
    customer_name: "CLIENTE A",
    customer_code: "000123",
    customer_store: "01",
    customer_order: "PO-1",
    order_type: "N",
    product_code: "90262910",
    ordered_quantity: 100,
    delivered_quantity: 40,
    open_quantity: 60,
    due_date: "2026-08-25",
    dispatch_date: "2026-08-20",
    product_stock: 10,
    allocated_stock: 10,
    covered_by_orders: 50,
    uncovered_quantity: 0,
    covering_orders: [],
    coverage_date: "2026-08-24",
    status: "covered_by_order",
    days_late: 0,
    ...overrides,
  };
}

describe("buildDemandExcelPayload", () => {
  it("inclui emissão do pedido junto com a entrega", () => {
    const payload = buildDemandExcelPayload([line()]);
    const keys = payload.columns.map((column) => column.key);
    expect(keys).toContain("issued");
    expect(keys).toContain("due");
    expect(payload.rows[0]?.issued).toBe("20/08/2026");
    expect(payload.rows[0]?.due).toBe("25/08/2026");
  });

  it("mantém quantidades numéricas para o Excel", () => {
    const payload = buildDemandExcelPayload([line()]);
    expect(payload.rows[0]?.ordered).toBe(100);
    expect(payload.rows[0]?.open).toBe(60);
  });

  it("deixa emissão vazia quando não há data de despacho/emissão", () => {
    const payload = buildDemandExcelPayload([line({ dispatch_date: null })]);
    expect(payload.rows[0]?.issued).toBe("");
  });
});
