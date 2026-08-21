import { describe, expect, it } from "vitest";

import type { DemandLine } from "../types";
import { buildDemandCsv } from "./demandCsv";

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

describe("buildDemandCsv", () => {
  it("usa ponto e vírgula e decimal com vírgula (Excel pt-BR)", () => {
    const [, row] = buildDemandCsv([line()]).split("\r\n");
    expect(row).toContain("25/08/2026;CLIENTE A;045123/01;PO-1;90262910");
    expect(row).toContain("100,000;40,000;60,000");
  });

  it("protege campo com ponto e vírgula ou aspas na razão social", () => {
    const [, row] = buildDemandCsv([line({ customer_name: 'CLIENTE "A"; LTDA' })]).split("\r\n");
    expect(row).toContain('"CLIENTE ""A""; LTDA"');
  });

  it("deixa a data vazia quando o pedido não tem entrega prometida", () => {
    const [, row] = buildDemandCsv([line({ due_date: null })]).split("\r\n");
    expect(row.startsWith(";CLIENTE A")).toBe(true);
  });

  it("escreve o cabeçalho uma única vez", () => {
    const rows = buildDemandCsv([line(), line({ sales_order: "045124" })]).split("\r\n");
    expect(rows).toHaveLength(3);
  });
});
