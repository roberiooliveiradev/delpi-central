import { describe, expect, it } from "vitest";

import type { ProductionOrderLine } from "../types";
import {
  buildProductionOrdersExcelPayload,
  buildProductionOrdersExportFileName,
  formatProductionOrdersExportDate,
} from "./productionOrdersExcel";

const LINE: ProductionOrderLine = {
  production_order: "24437001001",
  op_key: "24437001001",
  product_code: "90262031",
  product_description: "WEG MOT",
  issue_date: "2026-04-02",
  planned_start_date: "2026-10-28",
  due_date: "2026-10-28",
  finish_date: null,
  planned_qty: 0.1,
  pending_qty: 0.1,
  observation: "WEG_MOT",
  is_open: true,
  is_mother: true,
  branch: "01",
};

describe("buildProductionOrdersExcelPayload", () => {
  it("exporta as colunas operacionais da OP", () => {
    const payload = buildProductionOrdersExcelPayload([LINE], "01");
    expect(payload.title).toBe("OPS ABERTAS SC");
    expect(payload.columns.map((column) => column.key)).toEqual([
      "production_order",
      "product_code",
      "issue_date",
      "planned_start_date",
      "due_date",
      "planned_qty",
      "pending_qty",
      "observation",
    ]);
    expect(payload.rows[0]).toEqual({
      production_order: "24437001001",
      product_code: "90262031",
      issue_date: "02/04/2026",
      planned_start_date: "28/10/2026",
      due_date: "28/10/2026",
      planned_qty: 0.1,
      pending_qty: 0.1,
      observation: "WEG_MOT",
    });
  });

  it("usa o título da filial 02", () => {
    expect(buildProductionOrdersExcelPayload([LINE], "02").title).toBe("OPS ABERTAS ES");
  });

  it("inclui data fim só no recorte de OPs encerradas", () => {
    const payload = buildProductionOrdersExcelPayload(
      [{ ...LINE, finish_date: "2026-09-10", is_open: false }],
      "01",
      { includeFinishDate: true },
    );
    expect(payload.columns.map((column) => column.key)).toContain("finish_date");
    expect(payload.rows[0].finish_date).toBe("10/09/2026");
  });
});

describe("buildProductionOrdersExportFileName", () => {
  it("monta nome com data de emissão", () => {
    const issuedAt = new Date(2026, 8, 22);
    expect(formatProductionOrdersExportDate(issuedAt)).toBe("22-09-2026");
    expect(buildProductionOrdersExportFileName("01", issuedAt)).toBe("OPS ABERTAS SC - 22-09-2026");
    expect(buildProductionOrdersExportFileName("02", issuedAt)).toBe("OPS ABERTAS ES - 22-09-2026");
  });
});
