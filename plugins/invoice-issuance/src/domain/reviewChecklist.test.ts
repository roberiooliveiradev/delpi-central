import { describe, expect, it } from "vitest";
import { buildReviewChecklist } from "./reviewChecklist";
import type { Party } from "./types";

const party: Party = {
  party_type: "customer",
  party_code: "000001",
  party_store: "01",
  party_name: "ACME",
  tax_id: null,
  blocked: false,
};

describe("buildReviewChecklist", () => {
  it("marca conferência a partir dos dados já coletados", () => {
    const flags = buildReviewChecklist({
      party,
      items: [
        {
          product_code: "90260001",
          product_description: "Item",
          quantity: 2,
          unit_price: 10,
          stock_write_off: false,
        },
      ],
      invoiceType: "sale",
      invoiceTypeOther: "",
      freightMode: "cif",
      weightKg: "1.5",
      volumeCount: "2",
    });
    expect(Object.values(flags).every(Boolean)).toBe(true);
  });

  it("não exige o usuário marcar item a item", () => {
    const flags = buildReviewChecklist({
      party: null,
      items: [],
      invoiceType: "other",
      invoiceTypeOther: "",
      freightMode: "cif",
      weightKg: "",
      volumeCount: "",
    });
    expect(flags.recipient).toBe(false);
    expect(flags.item_codes).toBe(false);
    expect(flags.invoice_type).toBe(false);
  });
});
