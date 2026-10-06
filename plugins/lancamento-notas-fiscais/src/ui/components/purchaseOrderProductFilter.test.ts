import { describe, expect, it } from "vitest";
import type { NfeProductMappingView, OpenPurchaseOrderGroup } from "../../domain/types";
import {
  delpiProductCodesWhenFullyMapped,
  filterPurchaseOrderGroupsByProductCodes,
} from "./purchaseOrderProductFilter";

function group(order: string, items: Array<{ item: string; product: string; value: number }>): OpenPurchaseOrderGroup {
  return {
    order_number: order,
    delivery_date: "2026-10-10",
    issue_date: "2026-10-01",
    product_count: items.length,
    open_value: items.reduce((sum, item) => sum + item.value, 0),
    item_count: items.length,
    items: items.map((item) => ({
      branch: "01",
      order_number: order,
      order_item: item.item,
      product_code: item.product,
      product_description: item.product,
      supplier_part_number: "",
      warehouse: "01",
      unit: "UN",
      ordered_quantity: 1,
      delivered_quantity: 0,
      open_quantity: 1,
      pre_invoice_quantity: 0,
      issue_date: "2026-10-01",
      expected_delivery_date: "2026-10-10",
      supplier_code: "000001",
      supplier_store: "01",
      supplier_name: "Alpha",
      unit_price: item.value,
      open_merchandise_value: item.value,
      open_ipi_value: 0,
      open_freight_value: 0,
      open_discount_value: 0,
      open_value: item.value,
    })),
  };
}

const emptyReady: NfeProductMappingView = { status: "ready", detail: { items: [] } };

describe("filtro de pedido pelos produtos da NF-e", () => {
  it("só devolve códigos quando todos os itens estão relacionados", () => {
    expect(
      delpiProductCodesWhenFullyMapped({
        status: "ready",
        detail: {
          items: [
            { mappingStatus: "mapped", internalProductCode: "10080001" },
            { mappingStatus: "mapped", internalProductCode: "000050" },
            { mappingStatus: "mapped", internalProductCode: "10080001" },
          ],
        },
      }),
    ).toEqual(["10080001", "000050"]);
    expect(
      delpiProductCodesWhenFullyMapped({
        status: "ready",
        detail: {
          items: [
            { mappingStatus: "mapped", internalProductCode: "10080001" },
            { mappingStatus: "unmapped", internalProductCode: null },
          ],
        },
      }),
    ).toBeNull();
    expect(
      delpiProductCodesWhenFullyMapped({
        status: "ready",
        detail: {
          items: [{ mappingStatus: "ambiguous", internalProductCode: "10080001" }],
        },
      }),
    ).toBeNull();
    expect(delpiProductCodesWhenFullyMapped({ status: "loading" })).toBeNull();
    expect(delpiProductCodesWhenFullyMapped(emptyReady)).toBeNull();
  });

  it("mantém só as linhas dos códigos Delpi e o vínculo já gravado", () => {
    const groups = [
      group("000123", [
        { item: "0001", product: "00000000010080001", value: 10 },
        { item: "0002", product: "999", value: 30 },
      ]),
      group("000456", [{ item: "0001", product: "200", value: 5 }]),
    ];
    const filtered = filterPurchaseOrderGroupsByProductCodes(groups, ["10080001"]);
    expect(filtered.map((item) => item.order_number)).toEqual(["000123"]);
    expect(filtered[0].items.map((item) => item.order_item)).toEqual(["0001"]);
    expect(filtered[0].open_value).toBe(10);
    expect(filtered[0].product_count).toBe(1);

    const withLink = filterPurchaseOrderGroupsByProductCodes(groups, ["10080001"], [
      {
        order_number: "000456",
        delivery_date: "2026-10-10",
        lines: [{ order_item: "0001", product_code: "200" }],
      },
    ]);
    expect(withLink.map((item) => item.order_number)).toEqual(["000123", "000456"]);
  });
});
