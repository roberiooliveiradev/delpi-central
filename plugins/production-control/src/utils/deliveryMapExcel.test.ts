import { describe, expect, it } from "vitest";

import type { DeliveryMapRow, DeliveryMapSection } from "../types";
import {
  deliveryMapExcelCellValues,
  flattenDeliveryMapExcelRows,
} from "./deliveryMapExcel";

function row(overrides: Partial<DeliveryMapRow> = {}): DeliveryMapRow {
  return {
    production_order: "10737601001",
    product_code: "90262910",
    product_description: null,
    due_date: "2026-08-24",
    planned_qty: 6,
    produced_qty: 0,
    pending_qty: 6,
    observation: null,
    days_late: 0,
    is_delayed: false,
    mp_ok: false,
    work_center: "CDRL",
    is_reported: false,
    ...overrides,
  };
}

function section(
  sectionKey: string,
  rows: DeliveryMapRow[],
  label = sectionKey,
): DeliveryMapSection {
  return {
    section_key: sectionKey,
    label,
    due_date: "2026-08-24",
    row_count: rows.length,
    rows,
  };
}

describe("flattenDeliveryMapExcelRows", () => {
  it("repete cabeçalho por bloco e separa com linha em branco", () => {
    const flat = flattenDeliveryMapExcelRows([
      section("overdue_and_today", [row()], "Hoje + atrasadas"),
      section("2026-08-25", [row({ production_order: "10737601002" })], "25/08/2026"),
    ]);

    expect(flat.map((entry) => entry.kind)).toEqual([
      "header",
      "data",
      "blank",
      "header",
      "data",
    ]);
  });

  it("ignora seções vazias", () => {
    const flat = flattenDeliveryMapExcelRows([
      section("empty", []),
      section("overdue_and_today", [row()]),
    ]);

    expect(flat).toHaveLength(2);
    expect(flat[0]?.kind).toBe("header");
    expect(flat[1]?.kind).toBe("data");
  });
});

describe("deliveryMapExcelCellValues", () => {
  it("exporta as colunas visíveis na tela (sem MP-OK e CT)", () => {
    const values = deliveryMapExcelCellValues(
      row({
        observation: "apontada 1500",
        planned_qty: 6,
        pending_qty: 0.149,
      }),
    );

    expect(values).toEqual([
      "10737601001",
      "90262910",
      "24/08/2026",
      6,
      0.149,
      "apontada 1500",
    ]);
  });
});
