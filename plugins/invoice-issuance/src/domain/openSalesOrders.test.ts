import { describe, expect, it } from "vitest";
import {
  clampOpenQuantity,
  mergeIssuanceItems,
  salesOrderLineKey,
  toIssuanceItemFromOpenLine,
} from "./openSalesOrders";
import type { OpenSalesOrderLine } from "./types";

const line: OpenSalesOrderLine = {
  sales_order: "000111",
  sales_order_item: "01",
  customer_order_number: "PC-9",
  product_code: "90260001",
  product_description: "Conector",
  quantity_ordered: 10,
  quantity_delivered: 4,
  quantity_open: 6,
  unit_price: 12.5,
  open_amount: 75,
  stock_on_hand: 20,
};

describe("openSalesOrders", () => {
  it("não deixa quantidade passar do saldo", () => {
    expect(clampOpenQuantity(9, 6)).toBe(6);
    expect(clampOpenQuantity(2, 6)).toBe(2);
    expect(clampOpenQuantity(0, 6)).toBe(0);
  });

  it("monta item da solicitação a partir da linha do PV", () => {
    const item = toIssuanceItemFromOpenLine(line, 9);
    expect(item.quantity).toBe(6);
    expect(item.sales_order).toBe("000111");
    expect(item.sales_order_item).toBe("01");
    expect(item.unit_price).toBe(12.5);
    expect(item.stock_write_off).toBe(true);
    expect(toIssuanceItemFromOpenLine(line, 1, false).stock_write_off).toBe(false);
    expect(salesOrderLineKey(line)).toBe("000111|01");
  });

  it("substitui a mesma linha do PV e preserva avulsos", () => {
    const merged = mergeIssuanceItems(
      [
        {
          product_code: "AVULSO",
          product_description: "Avulso",
          quantity: 1,
          unit_price: 1,
          stock_write_off: false,
        },
        toIssuanceItemFromOpenLine(line, 2),
      ],
      [toIssuanceItemFromOpenLine(line, 4)],
    );
    expect(merged).toHaveLength(2);
    expect(merged[0].product_code).toBe("AVULSO");
    expect(merged[1].quantity).toBe(4);
  });
});
