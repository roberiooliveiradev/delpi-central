import { describe, expect, it } from "vitest";
import { applyDefaultStockWriteOff, defaultStockWriteOff } from "./stockWriteOff";

describe("defaultStockWriteOff", () => {
  it("marca baixa para venda e devolução", () => {
    expect(defaultStockWriteOff("sale")).toBe(true);
    expect(defaultStockWriteOff("return")).toBe(true);
  });

  it("não marca baixa para amostra, conserto e outros", () => {
    expect(defaultStockWriteOff("sample")).toBe(false);
    expect(defaultStockWriteOff("repair_shipment")).toBe(false);
    expect(defaultStockWriteOff("other")).toBe(false);
  });

  it("aplica o padrão do tipo em todos os itens", () => {
    const items = [
      {
        product_code: "A",
        product_description: "A",
        quantity: 1,
        unit_price: 1,
        stock_write_off: false,
      },
    ];
    expect(applyDefaultStockWriteOff(items, "sale")[0].stock_write_off).toBe(true);
    expect(applyDefaultStockWriteOff(items, "sample")[0].stock_write_off).toBe(false);
  });
});
