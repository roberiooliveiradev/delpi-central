import { describe, expect, it } from "vitest";

import { uniqueBuyerCodes, uniqueSupplierIdentities } from "./query";

describe("PC detail header — helpers de contexto", () => {
  it("uniqueSupplierIdentities deduplica por identidade (código, loja)", () => {
    const items = [
      { supplier_code: "000123", supplier_store: "01", supplier_name: "ACME" },
      { supplier_code: "000123", supplier_store: "01", supplier_name: "ACME" },
      { supplier_code: "000123", supplier_store: "02", supplier_name: "ACME" },
      { supplier_code: "000456", supplier_store: "01", supplier_name: "BETA" },
    ];
    const suppliers = uniqueSupplierIdentities(items);
    expect(suppliers).toHaveLength(3);
    expect(suppliers[0]).toEqual({
      code: "000123",
      store: "01",
      name: "ACME",
    });
    // Um único fornecedor (mesma loja) → uma identidade no cabeçalho.
    expect(
      uniqueSupplierIdentities([
        { supplier_code: "000123", supplier_store: "01", supplier_name: "ACME" },
        { supplier_code: " 000123 ", supplier_store: " 01 ", supplier_name: "ACME" },
      ]),
    ).toHaveLength(1);
  });

  it("uniqueSupplierIdentities ignora itens sem fornecedor e vazios", () => {
    expect(
      uniqueSupplierIdentities([
        { supplier_code: "", supplier_store: "", supplier_name: "" },
        {},
        { supplier_code: null },
      ]),
    ).toEqual([]);
    expect(uniqueSupplierIdentities(undefined)).toEqual([]);
    // Nome sem código ainda é identidade exibível.
    expect(
      uniqueSupplierIdentities([{ supplier_name: "FORNECEDOR X" }]),
    ).toHaveLength(1);
  });

  it("uniqueBuyerCodes deduplica compradores preservando zeros à esquerda", () => {
    const items = [
      { buyer_code: "001234" },
      { buyer_code: "001234" },
      { buyer_code: "  0099  " },
      { buyer_code: "" },
      { buyer_code: null },
      {},
    ];
    expect(uniqueBuyerCodes(items)).toEqual(["001234", "0099"]);
    expect(uniqueBuyerCodes(undefined)).toEqual([]);
    expect(uniqueBuyerCodes([{ buyer_code: " " }])).toEqual([]);
  });
});
