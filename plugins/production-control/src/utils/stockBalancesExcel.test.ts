import { describe, expect, it } from "vitest";

import type { StockBalanceLine } from "../types";
import {
  buildStockBalancesExcelPayload,
  buildStockBalancesExportFileName,
  formatStockBalancesExportDate,
  STOCK_BALANCES_EXCEL_QUANTITY_FACTOR,
} from "./stockBalancesExcel";

const LINE: StockBalanceLine = {
  product_code: "90260014",
  description: "CHIP",
  branch: "01",
  warehouse: "01",
  quantity: 12.5,
  unit_cost: 10.25,
  stock_value: 128.125,
};

describe("buildStockBalancesExcelPayload", () => {
  it("exporta só código e quantidade × 1000", () => {
    const payload = buildStockBalancesExcelPayload([LINE], "01");
    expect(payload.title).toBe("ESTOQUE MATRIZ");
    expect(payload.columns.map((column) => column.key)).toEqual(["product_code", "quantity"]);
    expect(payload.rows).toEqual([
      {
        product_code: "90260014",
        quantity: 12.5 * STOCK_BALANCES_EXCEL_QUANTITY_FACTOR,
      },
    ]);
  });

  it("usa título SALDO FILIAL na filial 02", () => {
    expect(buildStockBalancesExcelPayload([LINE], "02").title).toBe("SALDO FILIAL");
  });

  it("aceita lista vazia", () => {
    expect(buildStockBalancesExcelPayload([]).rows).toEqual([]);
  });
});

describe("buildStockBalancesExportFileName", () => {
  it("monta nome com data de emissão", () => {
    const issuedAt = new Date(2026, 7, 28);
    expect(formatStockBalancesExportDate(issuedAt)).toBe("28-08-2026");
    expect(buildStockBalancesExportFileName("01", issuedAt)).toBe("ESTOQUE MATRIZ - 28-08-2026");
    expect(buildStockBalancesExportFileName("02", issuedAt)).toBe("SALDO FILIAL - 28-08-2026");
  });
});
