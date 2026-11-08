import { describe, expect, it } from "vitest";

import {
  duplicateSupplierIndexes,
  emptySupplierRow,
  supplierHitLabel,
} from "./prcSuppliers";

describe("supplierHitLabel", () => {
  it("monta `code / store — name` preservando zeros à esquerda", () => {
    expect(
      supplierHitLabel({
        supplier_code: "000101",
        supplier_store: "01",
        supplier_name: "FORNECEDOR INDUSTRIAL",
      }),
    ).toBe("000101 / 01 — FORNECEDOR INDUSTRIAL");
  });

  it("tolera campos ausentes sem inventar conteúdo", () => {
    expect(supplierHitLabel({ supplier_code: "07" })).toBe("07 /  —");
  });
});

describe("duplicateSupplierIndexes", () => {
  it("marca vínculos com mesmo (supplierCode, store)", () => {
    const rows = [
      { ...emptySupplierRow(), supplierCode: "0001", store: "01" },
      { ...emptySupplierRow(), supplierCode: "0001", store: "02" },
      { ...emptySupplierRow(), supplierCode: "0001", store: "01" },
    ];
    expect([...duplicateSupplierIndexes(rows)].sort()).toEqual([0, 2]);
  });

  it("ignora linhas sem identidade completa", () => {
    const rows = [
      { ...emptySupplierRow(), supplierCode: "0001", store: "" },
      { ...emptySupplierRow(), supplierCode: "0001", store: "" },
    ];
    expect(duplicateSupplierIndexes(rows).size).toBe(0);
  });
});
